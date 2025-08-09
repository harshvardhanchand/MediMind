"""
Medical Correlation Engines
Comprehensive multi-domain correlation analysis for intelligent medical notifications
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.services.openfda_service import openfda_service
from app.utils.medical_utils import (
    medical_normalizer,
    medical_date_parser,
    normalize_drug_with_llm_or_fallback,
    normalize_symptom_with_llm_or_fallback,
)
from app.services.gemini_service import get_gemini_service, GeminiAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class DrugSymptomCorrelationEngine:
    """
    Analyzes correlations between medications and symptoms using FDA data + LLM fallback
    Optimized to avoid N×M scans and only query LLM for relevant pairs
    """

    def __init__(self):
        self.openfda_service = openfda_service

        # Deprecated: hardcoded fallbacks removed in favor of LLM fallback
        self.fallback_drug_effects = {}

        # Build indices (kept for compatibility; will be empty without hardcoded data)
        self._build_inverted_indices()

        # Lazy-initialized Gemini service
        self._gemini = None

    def _build_inverted_indices(self):
        """
        Build inverted indices: symptom → [drugs that can cause it]
        This optimizes from O(N×M) to O(K) where K = relevant matches
        """
        self.symptom_to_drugs_index = {}
        self.drug_to_symptoms_index = {}

        # Build fallback indices from hardcoded knowledge
        for drug_name, effects in self.fallback_drug_effects.items():
            normalized_drug = medical_normalizer.normalize_drug_name(drug_name)
            self.drug_to_symptoms_index[normalized_drug] = set()

            for symptom_name, effect_data in effects.items():
                normalized_symptom = medical_normalizer.normalize_symptom_name(
                    symptom_name
                )

                # Add to symptom → drugs mapping
                if normalized_symptom not in self.symptom_to_drugs_index:
                    self.symptom_to_drugs_index[normalized_symptom] = set()
                self.symptom_to_drugs_index[normalized_symptom].add(normalized_drug)

                # Add to drug → symptoms mapping
                self.drug_to_symptoms_index[normalized_drug].add(normalized_symptom)

                # Also add variations for better matching
                for variation in self._get_symptom_variations(symptom_name):
                    norm_variation = medical_normalizer.normalize_symptom_name(
                        variation
                    )
                    if norm_variation not in self.symptom_to_drugs_index:
                        self.symptom_to_drugs_index[norm_variation] = set()
                    self.symptom_to_drugs_index[norm_variation].add(normalized_drug)

    def _get_symptom_variations(self, symptom_name: str) -> List[str]:
        """Generate variations via LLM-normalized form only (no hardcoded map)."""
        try:
            # Use the LLM/fallback symptom normalizer to derive a single canonical form
            loop = asyncio.get_event_loop()
            canonical = loop.run_until_complete(
                normalize_symptom_with_llm_or_fallback(symptom_name)
            )
        except Exception:
            canonical = medical_normalizer.normalize_symptom_name(symptom_name)
        # Return just the original and canonical to avoid KB hardcoding
        variations = [symptom_name]
        if canonical and canonical != symptom_name:
            variations.append(canonical)
        return variations

    async def analyze(
        self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze drug-symptom correlations using FDA first, then LLM fallback
        """
        correlations = []

        try:
            # Try FDA-based correlations first
            fda_correlations = await self._analyze_with_fda_optimized(
                medications, symptoms
            )
            correlations.extend(fda_correlations)

            # Add LLM fallback correlations for pairs not covered by FDA
            llm_correlations = await self._analyze_with_llm_fallback(
                medications, symptoms, fda_correlations
            )
            correlations.extend(llm_correlations)

        except Exception as e:
            logger.error(f"FDA analysis failed, using LLM fallback only: {str(e)}")
            # If FDA fails, use LLM fallback across all pairs
            llm_correlations = await self._analyze_with_llm_fallback(
                medications, symptoms, []
            )
            correlations.extend(llm_correlations)

        return sorted(correlations, key=lambda x: x["confidence"], reverse=True)

    async def _analyze_with_fda_optimized(
        self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use OpenFDA service with optimized querying
        """
        correlations = []

        # Build medication index for faster lookups
        med_index = {}
        for med in medications:
            # Prefer async LLM-backed normalization via heuristic fallback
            try:
                normalized_name = await normalize_drug_with_llm_or_fallback(
                    med.get("name", "")
                )
            except Exception:
                normalized_name = medical_normalizer.normalize_drug_name(
                    med.get("name", "")
                )
            med_index[normalized_name] = med

        # For each symptom, check only against relevant drugs
        for symptom in symptoms:
            try:
                normalized_symptom = asyncio.get_event_loop().run_until_complete(
                    normalize_symptom_with_llm_or_fallback(symptom.get("symptom", ""))
                )
            except Exception:
                normalized_symptom = medical_normalizer.normalize_symptom_name(
                    symptom.get("symptom", "")
                )

            # Get candidate drugs for this symptom from our index
            candidate_drugs = self.symptom_to_drugs_index.get(normalized_symptom, set())

            # Also check an LLM-normalized symptom term only (no hardcoded FDA term expansions)
            fda_terms = [normalized_symptom]
            for term in fda_terms:
                norm_term = term
                candidate_drugs.update(
                    self.symptom_to_drugs_index.get(norm_term, set())
                )

            # If no candidates in our index, try all medications (for unknown drugs)
            if not candidate_drugs:
                candidate_drugs = set(med_index.keys())

            # Query FDA only for relevant drug-symptom pairs
            for drug_name in candidate_drugs:
                if drug_name in med_index:
                    medication = med_index[drug_name]
                    fda_result = await self._query_fda_for_symptom_correlation(
                        medication, symptom
                    )
                    if fda_result:
                        correlations.append(fda_result)

        return correlations

    async def _analyze_with_llm_fallback(
        self,
        medications: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        existing_correlations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini (gemini-2.0-flash) for pairs not covered by FDA; cap pairs per analysis and prefer recent/severe symptoms.
        """
        correlations: List[Dict[str, Any]] = []

        # Build med index
        med_index: Dict[str, Dict[str, Any]] = {}
        for med in medications:
            nd = medical_normalizer.normalize_drug_name(med.get("name", ""))
            if nd:
                med_index[nd] = med

        # Build already covered pairs
        covered = set()
        for corr in existing_correlations:
            med = corr.get("medication") or ""
            sym = corr.get("symptom") or ""
            if med and sym:
                covered.add(
                    (
                        medical_normalizer.normalize_drug_name(med),
                        medical_normalizer.normalize_symptom_name(sym),
                    )
                )

        # Score symptoms by recency/severity
        def symptom_score(s: Dict[str, Any]) -> float:
            sev = (s.get("severity") or "").lower()
            sev_w = 1.0
            if "sev" in sev:
                sev_w = 3.0
            elif "mod" in sev:
                sev_w = 2.0
            date_str = s.get("reported_date") or s.get("date")
            recency = 1.0
            try:
                dt = medical_date_parser.parse_medical_date(date_str, "symptom_report")
                if dt:
                    days_ago = (datetime.now() - dt).days
                    recency = max(0.5, 30.0 / (days_ago + 1))  # 0.5..30
            except Exception:
                pass
            return sev_w + min(3.0, recency)

        # Build candidate pairs
        pairs: List[tuple] = []
        for s in sorted(symptoms, key=symptom_score, reverse=True):
            ns = medical_normalizer.normalize_symptom_name(s.get("symptom", ""))
            if not ns:
                continue
            for nd, m in med_index.items():
                if (nd, ns) in covered:
                    continue
                pairs.append((m, s))

        # Cap pairs to limit latency/cost
        MAX_PAIRS = 6
        pairs = pairs[:MAX_PAIRS]

        for med, sym in pairs:
            try:
                corr = await self._query_llm_for_drug_symptom(med, sym)
                if corr:
                    correlations.append(corr)
            except Exception as e:
                logger.warning(
                    f"LLM fallback failed for {med.get('name')} + {sym.get('symptom')}: {str(e)}"
                )
                continue

        return correlations

    async def _query_fda_for_symptom_correlation(
        self, medication: Dict[str, Any], symptom: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Query FDA adverse events for drug-symptom correlation
        """
        try:
            drug_name = medication.get("name", "").lower().strip()
            symptom_name = symptom.get("symptom", "").lower().strip()

            # Use OpenFDA service to check for adverse events
            # We'll adapt the interaction API to work for symptom correlation
            result = await self._check_fda_adverse_events(drug_name, symptom_name)

            if result and result.get("total_events", 0) > 0:
                # Convert FDA data to correlation format
                correlation = self._convert_fda_to_correlation(
                    medication, symptom, result
                )
                return correlation

        except Exception as e:
            logger.warning(
                f"FDA query failed for {medication.get('name')} + {symptom.get('symptom')}: {str(e)}"
            )

        return None

    async def _check_fda_adverse_events(
        self, drug_name: str, symptom_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Direct FDA API call for drug-symptom adverse event correlation
        - Expanded to query brand/generic variants for the drug
        - Parallelized across symptom terms and drug variants
        """
        import aiohttp

        try:
            url = "https://api.fda.gov/drug/event.json"

            # Build candidate terms
            drug_candidates = medical_normalizer.get_comprehensive_drug_candidates(
                drug_name
            )
            drug_candidates = [d.lower().strip() for d in drug_candidates if d]

            symptom_search_terms = self._get_fda_symptom_terms(symptom_name)

            async with aiohttp.ClientSession() as session:
                tasks = []

                async def fetch(drug_term: str, symptom_term: str):
                    params = {
                        "search": f'patient.drug.medicinalproduct:"{drug_term}" AND patient.reaction.reactionmeddrapt:"{symptom_term}"',
                        "limit": 50,
                        "count": "patient.reaction.reactionmeddrapt.exact",
                    }
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("results"):
                                return self._parse_fda_symptom_data(
                                    drug_term, symptom_name, data
                                )
                        return None

                # Limit parallelism to avoid overload
                max_parallel = 6
                for d in drug_candidates:
                    for term in symptom_search_terms:
                        tasks.append(fetch(d, term))
                results: List[Optional[Dict[str, Any]]] = []
                for i in range(0, len(tasks), max_parallel):
                    chunk = tasks[i : i + max_parallel]
                    results.extend(
                        await asyncio.gather(*chunk, return_exceptions=False)
                    )
                    # Return first positive hit
                    for r in results[-len(chunk) :]:
                        if r:
                            return r

        except Exception as e:
            logger.error(f"FDA API call failed: {str(e)}")

        return None

    def _get_fda_symptom_terms(self, symptom_name: str) -> List[str]:
        """
        Convert common symptom names to FDA medical terminology
        """
        return medical_normalizer.get_fda_symptom_terms(symptom_name)

    def _parse_fda_symptom_data(
        self, drug_name: str, symptom_name: str, fda_data: Dict
    ) -> Dict[str, Any]:
        """
        Parse FDA adverse event data for symptom correlation
        """
        results = fda_data.get("results", [])

        total_reports = 0
        serious_reports = 0

        # Analyze the count data
        for result in results:
            count = result.get("count", 0)
            total_reports += count

        # Estimate confidence based on report frequency
        confidence = min(0.9, total_reports / 1000)  # Scale based on report count
        confidence = max(0.5, confidence)  # Minimum threshold for reporting

        return {
            "drug_name": drug_name,
            "symptom_name": symptom_name,
            "total_reports": total_reports,
            "confidence": confidence,
            "source": "FDA_ADVERSE_EVENTS",
            "data_quality": "high",
        }

    def _convert_fda_to_correlation(
        self,
        medication: Dict[str, Any],
        symptom: Dict[str, Any],
        fda_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert FDA adverse event data to correlation format
        """
        confidence = fda_result.get("confidence", 0.5)
        total_reports = fda_result.get("total_reports", 0)

        # Determine severity based on report frequency
        if total_reports > 500:
            severity = "high"
        elif total_reports > 100:
            severity = "medium"
        else:
            severity = "low"

        timing_score = self._calculate_timing_score(
            medication, symptom, {"onset_days": [1, 30]}
        )
        final_confidence = confidence * timing_score

        return {
            "type": "drug_symptom_correlation",
            "medication": medication.get("name"),
            "symptom": symptom.get("symptom"),
            "confidence": final_confidence,
            "severity": severity,
            "fda_reports": total_reports,
            "source": "FDA_VALIDATED",
            "timing_analysis": {
                "timing_score": timing_score,
                "expected_onset_days": [1, 30],
            },
            "recommendation": self._generate_fda_based_recommendation(
                medication, symptom, severity, total_reports
            ),
        }

    def _generate_fda_based_recommendation(
        self,
        medication: Dict[str, Any],
        symptom: Dict[str, Any],
        severity: str,
        report_count: int,
    ) -> str:
        """
        Generate FDA-based recommendation
        """
        med_name = medication.get("name")
        symptom_name = symptom.get("symptom")

        if severity == "high" or report_count > 500:
            return f"FDA data shows {symptom_name} is frequently reported with {med_name} ({report_count} reports). Contact your doctor immediately."
        elif severity == "medium" or report_count > 100:
            return f"FDA adverse event reports link {symptom_name} to {med_name} ({report_count} reports). Discuss with your healthcare provider."
        else:
            return f" FDA has {report_count} reports of {symptom_name} with {med_name}. Mention this to your doctor at your next visit."

    async def _query_llm_for_drug_symptom(
        self, medication: Dict[str, Any], symptom: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call Gemini with a strict JSON schema to evaluate if a symptom is a known side effect
        of the given medication. Returns a correlation dict compatible with the pipeline.
        """
        service = self._ensure_gemini()
        if not service:
            return None

        med_name = (medication.get("name") or "").strip()
        med_dosage = (medication.get("dosage") or "").strip()
        med_freq = (medication.get("frequency") or "").strip()
        med_start = medication.get("start_date")

        sym_name = (symptom.get("symptom") or "").strip()
        sym_date = symptom.get("reported_date") or symptom.get("date")

        prompt = f"""
        TASK: Determine if the given symptom is a known side effect of the medication.

        Return ONLY valid JSON with this exact schema (no extra text):
        {{
          "associated": true|false,
          "confidence": 0.0-1.0,
          "onset_days": [min_days, max_days],
          "severity": "low"|"medium"|"high",
          "recommendation": "short actionable message"
        }}

        Constraints:
        - Be conservative, evidence-based. If uncertain, set associated=false.
        - Use widely documented side-effect knowledge.
        - If associated=true, provide a reasonable onset window in days.

        INPUT:
        Medication: "{med_name}" Dosage: "{med_dosage}" Frequency: "{med_freq}" Start: "{med_start}"
        Symptom: "{sym_name}" Reported: "{sym_date}"
        """

        try:
            # Short timeout to bound latency
            raw = await asyncio.wait_for(
                service.analyze_medical_situation(prompt), timeout=4.0
            )
            data = service.parse_json_response(raw) if raw else {}

            if not data or not isinstance(data, dict):
                return None
            if not data.get("associated"):
                return None

            # Validate fields
            confidence = float(data.get("confidence", 0.0) or 0.0)
            if confidence < 0.6:
                return None
            onset = data.get("onset_days") or [1, 30]
            if not (isinstance(onset, list) and len(onset) == 2):
                onset = [1, 30]
            severity = (data.get("severity") or "medium").lower()
            recommendation = data.get("recommendation") or "Discuss with your doctor."

            # Timing score using onset window
            effect_data = {"onset_days": onset, "severity": severity}
            timing_score = self._calculate_timing_score(
                medication, symptom, effect_data
            )
            final_conf = min(0.95, max(0.5, confidence) * max(0.5, timing_score))

            return {
                "type": "drug_symptom_correlation",
                "medication": med_name,
                "symptom": sym_name,
                "confidence": final_conf,
                "severity": severity,
                "source": "LLM_FALLBACK",
                "timing_analysis": {
                    "timing_score": timing_score,
                    "expected_onset_days": onset,
                },
                "recommendation": recommendation,
            }
        except asyncio.TimeoutError:
            logger.warning("Gemini fallback timed out")
            return None
        except GeminiAPIError as ge:
            logger.warning(f"Gemini API error: {str(ge)}")
            return None
        except Exception as e:
            logger.error(f"LLM fallback exception: {str(e)}")
            return None

    def _ensure_gemini(self):
        if self._gemini is not None:
            return self._gemini
        try:
            self._gemini = get_gemini_service()
            return self._gemini
        except Exception as e:
            logger.warning(f"Gemini service unavailable: {str(e)}")
            self._gemini = None
            return None

    def _check_fallback_correlation(
        self, medication: Dict[str, Any], symptom: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check fallback hardcoded knowledge (reduced set)
        """
        drug_name = medication.get("name", "").lower().strip()
        symptom_name = symptom.get("symptom", "").lower().strip()

        # Normalize names using centralized utilities
        drug_name = medical_normalizer.normalize_drug_name(drug_name)
        symptom_name = medical_normalizer.normalize_symptom_name(symptom_name)

        if drug_name not in self.fallback_drug_effects:
            return None

        drug_effects = self.fallback_drug_effects[drug_name]

        # Check for matches
        matching_effect = None
        for effect_name, effect_data in drug_effects.items():
            if medical_normalizer.symptoms_match(symptom_name, effect_name):
                matching_effect = effect_data
                break

        if not matching_effect:
            return None

        # Calculate timing and confidence
        timing_score = self._calculate_timing_score(
            medication, symptom, matching_effect
        )
        base_confidence = matching_effect["confidence"]
        final_confidence = (
            base_confidence * timing_score * 0.9
        )  # Slightly lower confidence for fallback

        if final_confidence < 0.5:
            return None

        return {
            "type": "drug_symptom_correlation",
            "medication": medication.get("name"),
            "symptom": symptom.get("symptom"),
            "confidence": final_confidence,
            "severity": matching_effect["severity"],
            "source": "FALLBACK_KNOWLEDGE",
            "timing_analysis": {
                "timing_score": timing_score,
                "expected_onset_days": matching_effect["onset_days"],
            },
            "recommendation": self._generate_drug_symptom_recommendation(
                medication, symptom, matching_effect
            ),
        }

    def _calculate_timing_score(
        self,
        medication: Dict[str, Any],
        symptom: Dict[str, Any],
        effect_data: Dict[str, Any],
    ) -> float:
        """Calculate timing correlation score using robust date parsing"""
        try:
            med_start = medication.get("start_date")
            symptom_date = symptom.get("reported_date") or symptom.get("date")

            if not med_start or not symptom_date:
                return 0.8  # Default score when timing data unavailable

            # Use robust date parsing with appropriate context
            med_start_dt = medical_date_parser.parse_medical_date(
                med_start, "medication_start"
            )
            symptom_date_dt = medical_date_parser.parse_medical_date(
                symptom_date, "symptom_report"
            )

            if not med_start_dt or not symptom_date_dt:
                # Don't default to now() - return lower confidence instead
                logger.warning(
                    f"Could not parse dates for timing analysis: med_start={med_start}, symptom_date={symptom_date}"
                )
                return 0.6  # Lower confidence when timing cannot be analyzed

            days_diff = (symptom_date_dt - med_start_dt).days

            # Check if timing falls within expected onset window
            onset_range = effect_data["onset_days"]
            min_onset, max_onset = onset_range[0], onset_range[1]

            if days_diff < 0:
                return 0.1  # Symptom before medication - unlikely correlation
            elif min_onset <= days_diff <= max_onset:
                return 1.0  # Perfect timing
            elif days_diff < min_onset:
                # Too early, but still possible
                return 0.7
            elif days_diff > max_onset:
                # Late onset, decreasing probability
                excess_days = days_diff - max_onset
                if excess_days <= 30:
                    return 0.6
                elif excess_days <= 90:
                    return 0.4
                else:
                    return 0.2

        except Exception as e:
            logger.error(f"Error calculating timing score: {str(e)}")
            return 0.6  # Lower confidence on error, don't use current time

        return 0.8

    def _generate_drug_symptom_recommendation(
        self,
        medication: Dict[str, Any],
        symptom: Dict[str, Any],
        effect_data: Dict[str, Any],
    ) -> str:
        """Generate actionable recommendation"""
        severity = effect_data["severity"]
        med_name = medication.get("name")
        symptom_name = symptom.get("symptom")

        if severity == "high":
            return f"{symptom_name} may be a serious side effect of {med_name}. Contact your doctor immediately."
        elif severity == "medium":
            return f"{symptom_name} is a known side effect of {med_name}. Monitor and discuss with your healthcare provider."
        else:
            return f"{symptom_name} could be related to {med_name}. Mention this to your doctor at your next visit."


class LabSymptomCorrelationEngine:
    """
    Analyzes correlations between lab results and symptoms using LLM (no hardcoded patterns)
    """

    def __init__(self):
        # Max pairs to bound latency
        self.max_pairs = 6

    async def analyze(
        self, lab_results: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        LLM-backed analysis of lab-symptom correlations with bounded latency
        """
        correlations: List[Dict[str, Any]] = []

        # Build lab results index for faster lookups
        lab_index: Dict[str, List[Dict[str, Any]]] = {}
        for lab in lab_results:
            test_name = lab.get("test", "").lower().strip()
            if test_name not in lab_index:
                lab_index[test_name] = []
            lab_index[test_name].append(lab)

        # Score symptoms by recency/severity
        def symptom_score(s: Dict[str, Any]) -> float:
            sev = (s.get("severity") or "").lower()
            sev_w = 1.0
            if "sev" in sev:
                sev_w = 3.0
            elif "mod" in sev:
                sev_w = 2.0
            date_str = s.get("reported_date") or s.get("date")
            recency = 1.0
            try:
                dt = medical_date_parser.parse_medical_date(date_str, "symptom_report")
                if dt:
                    days_ago = (datetime.now() - dt).days
                    recency = max(0.5, 30.0 / (days_ago + 1))
            except Exception:
                pass
            return sev_w + min(3.0, recency)

        # Build candidate pairs (all labs × top symptoms), bounded
        pairs: List[tuple] = []
        for symptom in sorted(symptoms, key=symptom_score, reverse=True):
            # Normalize symptom name with LLM/fallback
            try:
                normalized_symptom = await normalize_symptom_with_llm_or_fallback(
                    symptom.get("symptom", "")
                )
            except Exception:
                normalized_symptom = medical_normalizer.normalize_symptom_name(
                    symptom.get("symptom", "")
                )
            if not normalized_symptom:
                continue
            # Pair with each available lab
            for test_name, labs in lab_index.items():
                for lab in labs:
                    pairs.append((lab, symptom, normalized_symptom))

        pairs = pairs[: self.max_pairs]

        for lab, symptom, normalized_symptom in pairs:
            correlation = await self._query_llm_for_lab_symptom(
                lab, symptom, normalized_symptom
            )
            if correlation:
                correlations.append(correlation)

        return sorted(correlations, key=lambda x: x.get("confidence", 0), reverse=True)

    async def _query_llm_for_lab_symptom(
        self,
        lab_result: Dict[str, Any],
        symptom: Dict[str, Any],
        normalized_symptom: str,
    ) -> Optional[Dict[str, Any]]:
        service = None
        try:
            service = get_gemini_service()
        except Exception:
            return None

        test_name = (lab_result.get("test") or "").strip()
        raw_value = lab_result.get("value")
        unit = lab_result.get("unit")
        norm_value = self._normalize_lab_value(test_name, raw_value, unit)
        if raw_value is None:
            return None

        sym_name = normalized_symptom
        date = lab_result.get("date")

        prompt = f"""
        TASK: Determine if the given lab test result could plausibly explain the patient's symptom.

        Return ONLY valid JSON with this exact schema:
        {{
          "associated": true|false,
          "confidence": 0.0-1.0,
          "direction": "high"|"low"|"normal",
          "mechanism": string,
          "recommendation": string
        }}

        Constraints:
        - Be conservative and evidence-based.
        - If uncertain, set associated=false.
        - Consider the lab value and unit provided.

        INPUT:
        Lab Test: "{test_name}" Value: "{raw_value}" Unit: "{unit}" NormalizedValue: "{norm_value}"
        Symptom: "{sym_name}" Date: "{date}"
        """
        try:
            raw = await asyncio.wait_for(
                service.analyze_medical_situation(prompt), timeout=2.5
            )
            data = service.parse_json_response(raw) if raw else {}
            if not isinstance(data, dict) or not data.get("associated"):
                return None
            try:
                conf = float(data.get("confidence", 0) or 0)
            except Exception:
                conf = 0.0
            if conf < settings.LLM_NORMALIZE_MIN_CONFIDENCE:
                return None
            direction = (data.get("direction") or "").lower()
            mechanism = data.get("mechanism") or ""
            recommendation = data.get("recommendation") or "Discuss with your doctor."

            return {
                "type": "lab_symptom_correlation",
                "lab_test": test_name,
                "lab_value": norm_value if norm_value is not None else raw_value,
                "symptom": sym_name,
                "confidence": min(0.95, max(0.5, conf)),
                "pattern_type": (
                    f"{direction}_pattern" if direction in {"high", "low"} else "normal"
                ),
                "mechanism": mechanism,
                "recommendation": recommendation,
            }
        except asyncio.TimeoutError:
            return None
        except GeminiAPIError:
            return None
        except Exception:
            return None

    def _normalize_lab_value(
        self, test_name: str, value: float, unit: Optional[str]
    ) -> Optional[float]:
        """
        Convert lab value to canonical units expected by thresholds.
        Canonical units:
        - glucose: mg/dL (convert mmol/L -> mg/dL by *18)
        - creatinine: mg/dL (convert µmol/L -> mg/dL by /88.4)
        - others: assume value provided matches canonical expectations or unitless
        """
        if value is None:
            return None
        if not unit:
            try:
                return float(value)
            except Exception:
                return None
        u = unit.strip().lower()
        t = test_name.strip().lower()
        try:
            if t == "glucose":
                if u in ["mmol/l", "mmol per l", "mmol/ l", "mmol\u002fl"]:
                    return float(value) * 18.0
                return float(value)  # mg/dL
            if t == "creatinine":
                if u in ["µmol/l", "umol/l", "micromol/l"]:
                    return float(value) / 88.4
                return float(value)  # mg/dL
            # Default pass-through
            return float(value)
        except Exception:
            return None


class DrugLabCorrelationEngine:
    """
    Analyzes correlations between medications and lab results using LLM (no hardcoded rules)
    """

    def __init__(self):
        # Max pairs to bound latency
        self.max_pairs = 6

    async def analyze(
        self, medications: List[Dict[str, Any]], lab_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        LLM-backed analysis of drug-lab effects with bounded latency
        """
        correlations: List[Dict[str, Any]] = []

        # Build indices for faster lookups
        med_index: Dict[str, List[Dict[str, Any]]] = {}
        for med in medications:
            try:
                normalized_name = await normalize_drug_with_llm_or_fallback(
                    med.get("name", "")
                )
            except Exception:
                normalized_name = medical_normalizer.normalize_drug_name(
                    med.get("name", "")
                )
            if normalized_name not in med_index:
                med_index[normalized_name] = []
            med_index[normalized_name].append(med)

        lab_index: Dict[str, List[Dict[str, Any]]] = {}
        for lab in lab_results:
            test_name = lab.get("test", "").lower().strip()
            if test_name not in lab_index:
                lab_index[test_name] = []
            lab_index[test_name].append(lab)

        # Build candidate pairs, bounded
        pairs: List[tuple] = []
        for drug_name, drug_list in med_index.items():
            for lab_test, labs in lab_index.items():
                for med in drug_list:
                    for lab in labs:
                        pairs.append((med, lab))
        pairs = pairs[: self.max_pairs]

        for med, lab in pairs:
            correlation = await self._query_llm_for_drug_lab(med, lab)
            if correlation:
                correlations.append(correlation)

        return sorted(
            correlations, key=lambda x: x.get("urgency_score", 0), reverse=True
        )

    async def _query_llm_for_drug_lab(
        self, medication: Dict[str, Any], lab_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        service = None
        try:
            service = get_gemini_service()
        except Exception:
            return None

        med_name = (medication.get("name") or "").strip()
        lab_name = (lab_result.get("test") or "").strip()
        value = lab_result.get("value")
        unit = lab_result.get("unit")

        prompt = f"""
        TASK: Determine if the medication affects the lab test (direction and clinical concern).

        Return ONLY valid JSON with this exact schema:
        {{
          "effect": "increases"|"decreases"|"monitor"|"none",
          "concern": "high"|"medium"|"monitor"|"none",
          "confidence": 0.0-1.0,
          "recommendation": string
        }}

        Constraints:
        - Be conservative and evidence-based.
        - If uncertain, pick "monitor" or "none" with low confidence.

        INPUT:
        Medication: "{med_name}"
        Lab: "{lab_name}" Value: "{value}" Unit: "{unit}"
        """
        try:
            raw = await asyncio.wait_for(
                service.analyze_medical_situation(prompt), timeout=2.5
            )
            data = service.parse_json_response(raw) if raw else {}
            if not isinstance(data, dict):
                return None
            effect = (data.get("effect") or "").lower()
            concern = (data.get("concern") or "").lower()
            try:
                conf = float(data.get("confidence", 0) or 0)
            except Exception:
                conf = 0.0
            if conf < settings.LLM_NORMALIZE_MIN_CONFIDENCE:
                return None

            urgency_map = {"high": 0.9, "medium": 0.6, "monitor": 0.3, "none": 0.0}
            urgency = urgency_map.get(concern, 0.0)
            recommendation = data.get("recommendation") or "Discuss with your doctor."

            return {
                "type": "drug_lab_correlation",
                "medication": med_name,
                "lab_test": lab_name,
                "lab_value": value,
                "effect_type": effect,
                "concern_level": concern,
                "urgency_score": urgency,
                "recommendation": recommendation,
            }
        except asyncio.TimeoutError:
            return None
        except GeminiAPIError:
            return None
        except Exception:
            return None


class TemporalPatternEngine:
    """
    Analyzes temporal patterns across all medical events
    """

    def analyze(self, medical_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze temporal patterns in medical events
        """
        patterns = []

        # Create timeline of all events
        timeline = self._create_unified_timeline(medical_profile)

        # Look for event clusters
        clusters = self._find_event_clusters(timeline)
        patterns.extend(clusters)

        # Look for sequential patterns
        sequences = self._find_sequential_patterns(timeline)
        patterns.extend(sequences)

        return sorted(patterns, key=lambda x: x.get("confidence", 0), reverse=True)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object using robust parsing - returns None if invalid"""
        parsed_date = medical_date_parser.parse_medical_date(date_str, "medical_event")
        if not parsed_date:
            logger.warning(f"Failed to parse date: {date_str}")
        return parsed_date

    def _create_unified_timeline(
        self, medical_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create unified timeline of all medical events"""
        timeline = []

        # Add medications
        for med in medical_profile.get("medications", []):
            if med.get("start_date"):
                parsed_date = self._parse_date(med["start_date"])
                if parsed_date:  # Only add if date is valid
                    timeline.append(
                        {
                            "date": med["start_date"],
                            "parsed_date": parsed_date,
                            "type": "medication_started",
                            "data": med,
                            "entity": "medication",
                        }
                    )

        # Add symptoms
        for symptom in medical_profile.get("recent_symptoms", []):
            symptom_date = symptom.get("reported_date") or symptom.get("date")
            if symptom_date:
                parsed_date = self._parse_date(symptom_date)
                if parsed_date:  # Only add if date is valid
                    timeline.append(
                        {
                            "date": symptom_date,
                            "parsed_date": parsed_date,
                            "type": "symptom_reported",
                            "data": symptom,
                            "entity": "symptom",
                        }
                    )

        # Add lab results
        for lab in medical_profile.get("lab_results", []):
            if lab.get("date"):
                parsed_date = self._parse_date(lab["date"])
                if parsed_date:  # Only add if date is valid
                    timeline.append(
                        {
                            "date": lab["date"],
                            "parsed_date": parsed_date,
                            "type": "lab_result",
                            "data": lab,
                            "entity": "lab",
                        }
                    )

        # Sort by parsed date
        timeline.sort(key=lambda x: x["parsed_date"])

        return timeline

    def _find_event_clusters(
        self, timeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find clusters of events in short timeframes"""
        clusters = []
        window_days = 7  # Look for events within 7 days

        for i, event in enumerate(timeline):
            cluster_events = [event]
            event_date = event["parsed_date"]  # Use pre-parsed date

            # Look for events within window
            for j in range(i + 1, len(timeline)):
                other_event = timeline[j]
                other_date = other_event["parsed_date"]  # Use pre-parsed date

                if (other_date - event_date).days <= window_days:
                    cluster_events.append(other_event)
                else:
                    break

            if len(cluster_events) >= 2:
                clusters.append(
                    {
                        "type": "temporal_cluster",
                        "events": cluster_events,
                        "timeframe_days": window_days,
                        "confidence": min(0.9, len(cluster_events) * 0.3),
                        "pattern_description": f"{len(cluster_events)} medical events within {window_days} days",
                        "recommendation": self._generate_cluster_recommendation(
                            cluster_events
                        ),
                    }
                )

        return clusters

    def _find_sequential_patterns(
        self, timeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find meaningful sequential patterns"""
        patterns = []

        # Look for medication -> symptom patterns
        for i, event in enumerate(timeline):
            if event["type"] == "medication_started":
                # Look for symptoms that follow
                med_date = event["parsed_date"]  # Use pre-parsed date

                for j in range(i + 1, len(timeline)):
                    if j >= len(timeline):
                        break

                    next_event = timeline[j]
                    if next_event["type"] == "symptom_reported":
                        symptom_date = next_event["parsed_date"]  # Use pre-parsed date
                        days_diff = (symptom_date - med_date).days

                        if (
                            1 <= days_diff <= 30
                        ):  # Reasonable timeframe for side effects
                            patterns.append(
                                {
                                    "type": "medication_symptom_sequence",
                                    "medication": event["data"],
                                    "symptom": next_event["data"],
                                    "days_between": days_diff,
                                    "confidence": 0.7,
                                    "pattern_description": f"Symptom appeared {days_diff} days after starting medication",
                                    "recommendation": f"Consider if {next_event['data'].get('symptom')} could be related to {event['data'].get('name')}",
                                }
                            )

        return patterns

    def _generate_cluster_recommendation(
        self, cluster_events: List[Dict[str, Any]]
    ) -> str:
        """Generate recommendation for event cluster"""
        event_types = [event["type"] for event in cluster_events]

        if "medication_started" in event_types and "symptom_reported" in event_types:
            return " Multiple medical events occurred close together. Consider if new symptoms could be related to medication changes."
        elif "lab_result" in event_types and "symptom_reported" in event_types:
            return " Lab results and symptoms occurred close together. Review if lab abnormalities explain symptoms."
        else:
            return f"{len(cluster_events)} medical events occurred within a short timeframe. Consider reviewing for connections."


class MultiCorrelationAnalyzer:
    """
    Master orchestrator for multi-domain correlation analysis
    """

    def __init__(self):
        self.drug_symptom_engine = DrugSymptomCorrelationEngine()
        self.lab_symptom_engine = LabSymptomCorrelationEngine()
        self.drug_lab_engine = DrugLabCorrelationEngine()
        self.temporal_engine = TemporalPatternEngine()

    async def analyze_comprehensive_correlations(
        self, medical_profile: Dict[str, Any], trigger_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive multi-domain correlation analysis
        """
        logger.info(
            f"Starting comprehensive correlation analysis for trigger: {trigger_event.get('type')}"
        )

        # Run all correlation engines (drug_symptom is async)
        correlations = {
            "drug_symptom": await self.drug_symptom_engine.analyze(
                medical_profile.get("medications", []),
                medical_profile.get("recent_symptoms", []),
            ),
            "lab_symptom": await self.lab_symptom_engine.analyze(
                medical_profile.get("lab_results", []),
                medical_profile.get("recent_symptoms", []),
            ),
            "drug_lab": await self.drug_lab_engine.analyze(
                medical_profile.get("medications", []),
                medical_profile.get("lab_results", []),
            ),
            "temporal_patterns": self.temporal_engine.analyze(medical_profile),
        }

        # Cross-validate and prioritize correlations
        validated_correlations = self._cross_validate_correlations(
            correlations, trigger_event
        )
        prioritized_correlations = self._prioritize_correlations(
            validated_correlations, trigger_event
        )

        # Generate comprehensive insights
        insights = self._generate_comprehensive_insights(
            prioritized_correlations, trigger_event
        )

        logger.info(
            f"Correlation analysis complete: {len(prioritized_correlations)} correlations found"
        )

        return {
            "correlations": prioritized_correlations,
            "insights": insights,
            "trigger_event": trigger_event,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def _cross_validate_correlations(
        self, correlations: Dict[str, List], trigger_event: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Cross-validate correlations across engines"""
        all_correlations = []

        # Flatten all correlations
        for engine_type, correlation_list in correlations.items():
            for correlation in correlation_list:
                correlation["engine"] = engine_type
                all_correlations.append(correlation)

        # Look for reinforcing correlations
        reinforced_correlations = []
        for correlation in all_correlations:
            # Check if other engines support this correlation
            supporting_evidence = self._find_supporting_evidence(
                correlation, all_correlations
            )

            if supporting_evidence:
                correlation["supporting_evidence"] = supporting_evidence
                correlation["confidence"] = min(
                    0.95, correlation["confidence"] * 1.2
                )  # Boost confidence

            reinforced_correlations.append(correlation)

        return reinforced_correlations

    def _find_supporting_evidence(
        self, target_correlation: Dict[str, Any], all_correlations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find correlations that support the target correlation"""
        supporting = []

        for correlation in all_correlations:
            if correlation == target_correlation:
                continue

            # Check for overlapping entities
            if self._correlations_overlap(target_correlation, correlation):
                supporting.append(
                    {
                        "engine": correlation["engine"],
                        "type": correlation["type"],
                        "confidence": correlation["confidence"],
                    }
                )

        return supporting

    def _correlations_overlap(
        self, corr1: Dict[str, Any], corr2: Dict[str, Any]
    ) -> bool:
        """Check if two correlations involve overlapping entities (split combo meds)"""

        def extract_entities(corr: Dict[str, Any]) -> set:
            entities = set()
            for key in ["medication", "symptom", "lab_test"]:
                val = corr.get(key)
                if not val:
                    continue
                # Split combo meds like "drugA + drugB"
                if key == "medication" and "+" in str(val):
                    parts = [p.strip().lower() for p in str(val).split("+")]
                    entities.update(parts)
                else:
                    entities.add(str(val).lower())
            return entities

        entities1 = extract_entities(corr1)
        entities2 = extract_entities(corr2)
        return bool(entities1.intersection(entities2))

    def _prioritize_correlations(
        self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prioritize correlations based on multiple factors"""

        for correlation in correlations:
            priority_score = self._calculate_priority_score(correlation, trigger_event)
            correlation["priority_score"] = priority_score

        return sorted(correlations, key=lambda x: x["priority_score"], reverse=True)

    def _calculate_priority_score(
        self, correlation: Dict[str, Any], trigger_event: Dict[str, Any]
    ) -> float:
        """Calculate priority score for correlation"""
        score = 0.0

        # Base confidence (40% of score)
        base_confidence = correlation.get("confidence", 0.5)
        score += 0.4 * base_confidence

        # Severity/concern level (30% of score)
        severity = correlation.get("severity", "low")
        concern_level = correlation.get("concern_level", "none")

        if severity == "high" or concern_level == "high":
            score += 0.3 * 1.0
        elif severity == "medium" or concern_level == "medium":
            score += 0.3 * 0.7
        else:
            score += 0.3 * 0.4

        # Relevance to trigger event (20% of score)
        relevance = self._calculate_trigger_relevance(correlation, trigger_event)
        score += 0.2 * relevance

        # Supporting evidence (10% of score)
        supporting_count = len(correlation.get("supporting_evidence", []))
        score += 0.1 * min(1.0, supporting_count * 0.5)

        return min(1.0, score)

    def _calculate_trigger_relevance(
        self, correlation: Dict[str, Any], trigger_event: Dict[str, Any]
    ) -> float:
        """Calculate how relevant correlation is to the trigger event"""
        trigger_type = trigger_event.get("type", "")

        # Higher relevance if correlation involves the trigger entity
        if trigger_type == "symptom_reported":
            trigger_symptom = trigger_event.get("symptom", "").lower()
            if correlation.get("symptom", "").lower() == trigger_symptom:
                return 1.0
        elif trigger_type == "medication_added":
            trigger_med = trigger_event.get("medication", "").lower()
            if correlation.get("medication", "").lower() == trigger_med:
                return 1.0
        elif trigger_type == "lab_result":
            trigger_lab = trigger_event.get("lab_test", "").lower()
            if correlation.get("lab_test", "").lower() == trigger_lab:
                return 1.0

        return 0.5  # Default relevance

    def _generate_comprehensive_insights(
        self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive insights from all correlations"""

        # Take top correlations for insights
        top_correlations = correlations[:5]

        insights = {
            "summary": self._generate_summary_insight(top_correlations, trigger_event),
            "recommendations": self._generate_actionable_recommendations(
                top_correlations
            ),
            "risk_alerts": self._generate_risk_alerts(top_correlations),
            "monitoring_suggestions": self._generate_monitoring_suggestions(
                top_correlations
            ),
        }

        return insights

    def _generate_summary_insight(
        self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]
    ) -> str:
        """Generate summary insight"""
        if not correlations:
            return f"No significant correlations found for {trigger_event.get('type', 'this event')}."

        high_priority = [c for c in correlations if c.get("priority_score", 0) > 0.8]

        if high_priority:
            return f"Found {len(high_priority)} high-priority medical correlations that may require attention."
        else:
            return f"Found {len(correlations)} potential medical correlations worth monitoring."

    def _generate_actionable_recommendations(
        self, correlations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        for correlation in correlations[:3]:  # Top 3 correlations
            if correlation.get("recommendation"):
                recommendations.append(correlation["recommendation"])

        return recommendations

    def _generate_risk_alerts(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate risk alerts"""
        alerts = []

        for correlation in correlations:
            if (
                correlation.get("severity") == "high"
                or correlation.get("concern_level") == "high"
                or correlation.get("priority_score", 0) > 0.85
            ):

                alert = f"HIGH RISK: {correlation.get('type', 'Medical correlation')} detected"
                if correlation.get("medication"):
                    alert += f" involving {correlation['medication']}"
                alerts.append(alert)

        return alerts

    def _generate_monitoring_suggestions(
        self, correlations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate monitoring suggestions"""
        suggestions = []

        monitoring_items = set()
        for correlation in correlations:
            if correlation.get("monitoring_recommendation"):
                monitoring_items.add(correlation["monitoring_recommendation"])

        return list(monitoring_items)


# Global instance
multi_correlation_analyzer = MultiCorrelationAnalyzer()
