"""
Medical Utilities
Centralized normalization and matching functions for medical data
"""

import re
from typing import List, Optional, Tuple
from functools import lru_cache
from datetime import datetime
import logging
import asyncio
import time

from app.core.config import settings
from app.services.gemini_service import get_gemini_service, GeminiAPIError
from cachetools import TTLCache

logger = logging.getLogger(__name__)


# Replace custom TTL cache with library TTLCache
_llm_norm_cache: TTLCache = TTLCache(
    maxsize=settings.LLM_NORMALIZE_CACHE_MAXSIZE,
    ttl=settings.LLM_NORMALIZE_CACHE_TTL_SEC,
)


def _heuristic_normalize_drug(drug_name: str) -> str:
    if not drug_name:
        return ""
    s = drug_name.lower().strip()
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|units?)\b", "", s)
    s = re.sub(r"[-_ ]?(mg|mcg|g|ml|units?)$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    tokens = s.split()
    release_suffixes = {"er", "xr", "sr", "cr", "la", "xl"}
    if tokens and tokens[-1] in release_suffixes:
        tokens = tokens[:-1]
    s = " ".join(tokens)
    s = re.sub(r"[^a-z+ ]", "", s).strip()
    if len(s) < 3 and drug_name:
        return drug_name.lower().strip()
    return s


def _heuristic_normalize_symptom(symptom: str) -> str:
    if not symptom:
        return ""
    s = symptom.lower().strip()
    s = re.sub(r"[_-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for prefix in ["feeling ", "experiencing ", "having "]:
        if s.startswith(prefix):
            s = s[len(prefix) :]
            break
    s = re.sub(r"[^a-z ]", "", s).strip()
    return s


async def _llm_normalize(kind: str, value: str) -> Optional[Tuple[str, float]]:
    """
    kind: "drug" | "symptom"
    Returns (canonical, confidence) or None on failure/timeout.
    """
    try:
        service = get_gemini_service()
    except Exception as e:
        logger.debug(f"LLM service unavailable: {e}")
        return None

    if not value:
        return None

    prompt = (
        "You are a normalizer. Return only JSON.\n"
        'Schema: {\n  "canonical": string,\n  "confidence": number\n}\n'
        "Rules:\n- For drugs: return the INN/generic (non-brand) name without dosage or units.\n"
        "- For symptoms: return a concise clinical term.\n"
        "- Use lowercase, no extra commentary.\n"
        f'Input {kind}: "{value}"\n'
    )

    timeout_sec = max(0.2, settings.LLM_NORMALIZE_TIMEOUT_MS / 1000.0)
    try:
        raw = await asyncio.wait_for(
            service.analyze_medical_situation(prompt), timeout=timeout_sec
        )
        data = service.parse_json_response(raw) if raw else {}
        if not isinstance(data, dict):
            return None
        canonical = (data.get("canonical") or "").strip().lower()
        try:
            confidence = float(data.get("confidence", 0) or 0)
        except Exception:
            confidence = 0.0
        if not canonical:
            return None
        return canonical, confidence
    except asyncio.TimeoutError:
        logger.debug("LLM normalize timeout")
        return None
    except GeminiAPIError as ge:
        logger.debug(f"LLM normalize API error: {ge}")
        return None
    except Exception as e:
        logger.debug(f"LLM normalize error: {e}")
        return None


async def normalize_drug_with_llm_or_fallback(drug_name: str) -> str:
    key = ("drug", drug_name or "")
    cached = _llm_norm_cache.get(key)
    if cached is not None:
        return cached

    if not settings.LLM_NORMALIZATION_ENABLED:
        result = _heuristic_normalize_drug(drug_name)
        _llm_norm_cache[key] = result
        return result

    result = _heuristic_normalize_drug(drug_name)
    llm = await _llm_normalize("drug", drug_name)
    if llm:
        canonical, conf = llm
        if conf >= settings.LLM_NORMALIZE_MIN_CONFIDENCE:
            result = canonical
    _llm_norm_cache[key] = result
    return result


async def normalize_symptom_with_llm_or_fallback(symptom: str) -> str:
    key = ("symptom", symptom or "")
    cached = _llm_norm_cache.get(key)
    if cached is not None:
        return cached

    if not settings.LLM_NORMALIZATION_ENABLED:
        result = _heuristic_normalize_symptom(symptom)
        _llm_norm_cache[key] = result
        return result

    result = _heuristic_normalize_symptom(symptom)
    llm = await _llm_normalize("symptom", symptom)
    if llm:
        canonical, conf = llm
        if conf >= settings.LLM_NORMALIZE_MIN_CONFIDENCE:
            result = canonical
    _llm_norm_cache[key] = result
    return result


class MedicalNormalizer:
    """
    Centralized medical data normalization and matching
    """

    def __init__(self):

        self.drug_aliases = {}

        # Symptom mappings and variations
        self.symptom_mappings = {}

        self.fda_symptom_terms = {}

        self.drug_suffixes = ["er", "xl", "cr", "sr", "la", "xr", "mg", "mcg", "g"]

    @lru_cache(maxsize=2000)
    def normalize_drug_name(self, drug_name: str) -> str:
        """
        LLM-backed normalization with heuristic fallback and compatibility with existing alias map.
        """
        if not drug_name:
            return ""
        # Fast path cache via async helper isn't available here; do a best-effort sync heuristic, then return.
        # Call sites that can await should prefer normalize_drug_with_llm_or_fallback.
        normalized = _heuristic_normalize_drug(drug_name)
        # Apply legacy alias mapping for backward compatibility
        if normalized in self.drug_aliases:
            return self.drug_aliases[normalized]
        return normalized

    @lru_cache(maxsize=1000)
    def normalize_symptom_name(self, symptom_name: str) -> str:
        """
        Heuristic normalization; async call sites should use normalize_symptom_with_llm_or_fallback for LLM.
        """
        if not symptom_name:
            return ""
        normalized = _heuristic_normalize_symptom(symptom_name)
        if normalized in self.symptom_mappings:
            return self.symptom_mappings[normalized]
        without_underscores = normalized.replace("_", "")
        if without_underscores in self.symptom_mappings:
            return self.symptom_mappings[without_underscores]
        return normalized

    def symptoms_match(self, reported_symptom: str, known_effect: str) -> bool:
        """
        Check if reported symptom matches known drug effect
        """

        norm_reported = self.normalize_symptom_name(reported_symptom)
        norm_known = self.normalize_symptom_name(known_effect)

        if norm_reported == norm_known:
            return True

        partial_matches = [
            ("muscle", "muscle"),
            ("stomach", "stomach"),
            ("nausea", "nausea"),
            ("dizz", "dizz"),
            ("fatigue", "tired"),
            ("tired", "fatigue"),
            ("cough", "cough"),
            ("pain", "pain"),
            ("ache", "pain"),
            ("ache", "ache"),
        ]

        for pattern1, pattern2 in partial_matches:
            if pattern1 in norm_reported and pattern2 in norm_known:
                return True
            if pattern2 in norm_reported and pattern1 in norm_known:
                return True

        return False

    def get_fda_symptom_terms(self, symptom_name: str) -> List[str]:
        """
        Convert symptom name to FDA medical terminology
        """
        normalized = self.normalize_symptom_name(symptom_name)

        if normalized in self.fda_symptom_terms:
            return self.fda_symptom_terms[normalized]

        return [normalized, symptom_name.lower()]

    def fuzzy_match_drug(
        self, drug_name: str, known_drugs: List[str], threshold: float = 0.8
    ) -> Optional[str]:
        """
        Fuzzy matching for drug names using basic similarity metrics
        """
        return self._fuzzy_match_basic(drug_name, known_drugs, threshold)

    def _fuzzy_match_basic(
        self, drug_name: str, known_drugs: List[str], threshold: float = 0.8
    ) -> Optional[str]:
        """
        Fallback fuzzy matching using multiple similarity metrics
        """
        normalized_input = self.normalize_drug_name(drug_name)
        best_match = None
        best_score = 0.0

        for known_drug in known_drugs:
            normalized_known = self.normalize_drug_name(known_drug)

            jaccard_score = self._calculate_jaccard_similarity(
                normalized_input, normalized_known
            )
            levenshtein_score = self._calculate_levenshtein_similarity(
                normalized_input, normalized_known
            )

            combined_score = (jaccard_score * 0.6) + (levenshtein_score * 0.4)

            if combined_score > best_score and combined_score >= threshold:
                best_score = combined_score
                best_match = known_drug

        return best_match

    def _calculate_jaccard_similarity(self, str1: str, str2: str) -> float:
        """
        Jaccard similarity on character bigrams (existing implementation)
        """
        if not str1 or not str2:
            return 0.0

        if str1 == str2:
            return 1.0

        bigrams1 = set(str1[i : i + 2] for i in range(len(str1) - 1))
        bigrams2 = set(str2[i : i + 2] for i in range(len(str2) - 1))

        if not bigrams1 and not bigrams2:
            return 1.0

        if not bigrams1 or not bigrams2:
            return 0.0

        intersection = len(bigrams1.intersection(bigrams2))
        union = len(bigrams1.union(bigrams2))

        return intersection / union if union > 0 else 0.0

    def _calculate_levenshtein_similarity(self, str1: str, str2: str) -> float:
        """
        Simple Levenshtein distance similarity
        """
        if not str1 or not str2:
            return 0.0

        if str1 == str2:
            return 1.0

        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                s1, s2 = s2, s1

            distances = range(len(s2) + 1)
            for i1, c1 in enumerate(s1):
                new_distances = [i1 + 1]
                for i2, c2 in enumerate(s2):
                    if c1 == c2:
                        new_distances.append(distances[i2])
                    else:
                        new_distances.append(
                            1 + min(distances[i2], distances[i2 + 1], new_distances[-1])
                        )
                distances = new_distances
            return distances[-1]

        max_len = max(len(str1), len(str2))
        distance = levenshtein_distance(str1, str2)

        return 1.0 - (distance / max_len)

    def get_comprehensive_drug_candidates(self, drug_name: str) -> List[str]:
        """
        Get comprehensive list of drug name candidates including variations and fuzzy matches
        """
        candidates = []
        candidates.append(drug_name)
        normalized = self.normalize_drug_name(drug_name)
        if normalized != drug_name:
            candidates.append(normalized)
        if normalized in self.drug_aliases:
            candidates.append(self.drug_aliases[normalized])
        for alias, canonical in self.drug_aliases.items():
            if canonical == normalized or alias == normalized:
                candidates.append(canonical)
                candidates.append(alias)
        unique_candidates = []
        seen = set()
        for candidate in candidates:
            candidate_lower = candidate.lower() if candidate else ""
            if candidate and candidate_lower not in seen:
                unique_candidates.append(candidate)
                seen.add(candidate_lower)
        return unique_candidates


class MedicalDateParser:
    """
    Robust date parsing for medical data using python-dateutil
    """

    @staticmethod
    def parse_medical_date(
        date_input: str, context: str = "medical_event"
    ) -> Optional[datetime]:
        """
        Parse medical date using python-dateutil with proper validation
        """
        if not date_input:
            return None

        try:
            from dateutil import parser as dateutil_parser
            from datetime import datetime

            if isinstance(date_input, str):
                current_year = datetime.now().year
                default_date = datetime(current_year, 1, 1)
                parsed_date = dateutil_parser.parse(
                    date_input, default=default_date, fuzzy=False
                )
                if not MedicalDateParser._is_valid_medical_date(parsed_date, context):
                    logger.warning(
                        f"Date out of valid range for {context}: {parsed_date}"
                    )
                    return None
                return parsed_date
            elif isinstance(date_input, datetime):
                if MedicalDateParser._is_valid_medical_date(date_input, context):
                    return date_input
                else:
                    logger.warning(
                        f"Datetime out of valid range for {context}: {date_input}"
                    )
                    return None
        except Exception as e:
            logger.warning(
                f"Failed to parse date '{date_input}' for {context}: {str(e)}"
            )
        return None

    @staticmethod
    def _is_valid_medical_date(date: datetime, context: str) -> bool:
        from datetime import datetime, timedelta

        now = datetime.now()
        if context == "medication_start":
            min_date = datetime(1950, 1, 1)
            max_date = now + timedelta(days=365)
        elif context == "lab_result":
            min_date = datetime(1960, 1, 1)
            max_date = now + timedelta(days=30)
        elif context == "symptom_report":
            min_date = datetime(1900, 1, 1)
            max_date = now
        else:
            min_date = datetime(1900, 1, 1)
            max_date = now + timedelta(days=365)
        return min_date <= date <= max_date


medical_normalizer = MedicalNormalizer()
medical_date_parser = MedicalDateParser()
