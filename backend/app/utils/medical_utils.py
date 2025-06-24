"""
Medical Utilities
Centralized normalization and matching functions for medical data
"""

import re
from typing import List, Optional
from functools import lru_cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MedicalNormalizer:
    """
    Centralized medical data normalization and matching
    """
    
    def __init__(self):
        
        self.drug_aliases = {
            "paracetamol": "acetaminophen",
            "tylenol": "acetaminophen",
            "advil": "ibuprofen",
            "motrin": "ibuprofen",
            "zestril": "lisinopril",
            "prinivil": "lisinopril",
            "lopressor": "metoprolol",
            "toprol": "metoprolol",
            "glucophage": "metformin",
            "lipitor": "atorvastatin",
            "coumadin": "warfarin",
            "amoxil": "amoxicillin"
        }
        
        # Symptom mappings and variations
        self.symptom_mappings = {
            "tired": "fatigue",
            "exhausted": "fatigue",
            "sleepy": "fatigue",
            "drowsy": "fatigue",
            "lightheaded": "dizziness",
            "light_headed": "dizziness",
            "dizzy": "dizziness",
            "vertigo": "dizziness",
            "upset_stomach": "stomach_upset",
            "stomach_pain": "stomach_upset",
            "abdominal_pain": "stomach_upset",
            "muscle_ache": "muscle_pain",
            "muscle_aches": "muscle_pain",
            "myalgia": "muscle_pain",
            "joint_pain": "muscle_pain",
            "arthralgia": "muscle_pain",
            "sick_to_stomach": "nausea",
            "queasy": "nausea",
            "throw_up": "vomiting",
            "throwing_up": "vomiting",
            "dry_cough": "cough",
            "persistent_cough": "cough",
            "chronic_cough": "cough"
        }
        
        
        self.fda_symptom_terms = {
            "dizziness": ["dizziness", "vertigo", "lightheadedness"],
            "fatigue": ["fatigue", "asthenia", "weakness"],
            "nausea": ["nausea", "vomiting"],
            "headache": ["headache", "cephalgia"],
            "cough": ["cough", "cough dry"],
            "muscle_pain": ["myalgia", "muscle pain", "arthralgia"],
            "stomach_upset": ["abdominal pain", "dyspepsia", "stomach discomfort"],
            "rash": ["rash", "skin rash", "dermatitis"],
            "swelling": ["oedema", "edema", "swelling"],
            "confusion": ["confusion", "mental status changes"]
        }
        
        
        self.drug_suffixes = ["er", "xl", "cr", "sr", "la", "xr", "mg", "mcg", "g"]
    
    @lru_cache(maxsize=2000)
    def normalize_drug_name(self, drug_name: str) -> str:
        """
        Robust drug name normalization with proper edge case handling
        """
        if not drug_name:
            return ""
        
        
        normalized = drug_name.lower().strip()
        
       
        normalized = re.sub(r'\([^)]*\)', '', normalized).strip()
        
        
        
        
        normalized = re.sub(r'\b\d+\s*(mg|mcg|g|ml|units?)\b', '', normalized)
        
        
        normalized = re.sub(r'\d+(mg|mcg|g|ml|units?)\b', '', normalized)
        
        
        normalized = re.sub(r'\s+(mg|mcg|g|ml|units?)\b', '', normalized)
        
        
        normalized = re.sub(r'[-_](mg|mcg|g|ml|units?)$', '', normalized)
        
       
        for unit in ['mg', 'mcg', 'ml', 'units', 'unit']:
            if normalized.endswith(unit) and len(normalized) > len(unit) + 3:
                
                candidate = normalized[:-len(unit)]
               
                if not any(candidate.endswith(ending) for ending in ['ing', 'ling', 'ring', 'ding', 'ping']):
                    normalized = candidate
                    break
        
        
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        
        if normalized in self.drug_aliases:
            return self.drug_aliases[normalized]
        
        
        original_normalized = normalized
        for suffix in self.drug_suffixes:
            
            pattern = rf'\b{re.escape(suffix)}$'
            if re.search(pattern, normalized):
                candidate = re.sub(pattern, '', normalized).strip()
                if candidate and len(candidate) > 2:  
                    normalized = candidate
                    break
        
        
        if normalized in self.drug_aliases:
            return self.drug_aliases[normalized]
        
       
        if len(normalized) < 3 and len(original_normalized) >= 3:
            normalized = original_normalized
        
        return normalized
    
    @lru_cache(maxsize=1000)
    def normalize_symptom_name(self, symptom_name: str) -> str:
        """
        Normalize symptom name with caching for performance
        """
        if not symptom_name:
            return ""
        
        
        normalized = symptom_name.lower().replace(" ", "_").strip()
        
        
        prefixes_to_remove = ["feeling_", "experiencing_", "having_"]
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        
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
            ("ache", "ache")
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
    
    def fuzzy_match_drug(self, drug_name: str, known_drugs: List[str], threshold: float = 0.8) -> Optional[str]:
        """
        Fuzzy matching for drug names using basic similarity metrics
        """
        return self._fuzzy_match_basic(drug_name, known_drugs, threshold)
    
    def _fuzzy_match_basic(self, drug_name: str, known_drugs: List[str], threshold: float = 0.8) -> Optional[str]:
        """
        Fallback fuzzy matching using multiple similarity metrics
        """
        normalized_input = self.normalize_drug_name(drug_name)
        best_match = None
        best_score = 0.0
        
        for known_drug in known_drugs:
            normalized_known = self.normalize_drug_name(known_drug)
            
            
            jaccard_score = self._calculate_jaccard_similarity(normalized_input, normalized_known)
            levenshtein_score = self._calculate_levenshtein_similarity(normalized_input, normalized_known)
            
            
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
        
        # Character bigrams
        bigrams1 = set(str1[i:i+2] for i in range(len(str1)-1))
        bigrams2 = set(str2[i:i+2] for i in range(len(str2)-1))
        
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
        
        # Simple Levenshtein distance calculation
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
                        new_distances.append(1 + min(distances[i2], distances[i2 + 1], new_distances[-1]))
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
        
        # Add original name
        candidates.append(drug_name)
        
        # Add normalized version
        normalized = self.normalize_drug_name(drug_name)
        if normalized != drug_name:
            candidates.append(normalized)
        
        # Add direct aliases if found
        if normalized in self.drug_aliases:
            candidates.append(self.drug_aliases[normalized])
        
        # Add reverse lookup from aliases
        for alias, canonical in self.drug_aliases.items():
            if canonical == normalized or alias == normalized:
                candidates.append(canonical)
                candidates.append(alias)
        
        # Remove duplicates while preserving order
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
    def parse_medical_date(date_input: str, context: str = "medical_event") -> Optional[datetime]:
        """
        Parse medical date using python-dateutil with proper validation
        """
        if not date_input:
            return None
        
        try:
            from dateutil import parser as dateutil_parser
            from datetime import datetime
            
            # Handle string dates
            if isinstance(date_input, str):
                # Use dateutil's robust parser with reasonable default
                # Default to January 1st of current year at midnight for missing components
                current_year = datetime.now().year
                default_date = datetime(current_year, 1, 1)
                
                parsed_date = dateutil_parser.parse(date_input, default=default_date, fuzzy=False)
                
                # Validate date range - medical events should be reasonable
                if not MedicalDateParser._is_valid_medical_date(parsed_date, context):
                    logger.warning(f"Date out of valid range for {context}: {parsed_date}")
                    return None
                
                return parsed_date
            
            # If already datetime, validate and return
            elif isinstance(date_input, datetime):
                if MedicalDateParser._is_valid_medical_date(date_input, context):
                    return date_input
                else:
                    logger.warning(f"Datetime out of valid range for {context}: {date_input}")
                    return None
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_input}' for {context}: {str(e)}")
        
        return None
    
    @staticmethod
    def _is_valid_medical_date(date: datetime, context: str) -> bool:
        """
        Validate that a date is within reasonable bounds for medical data
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Define reasonable date ranges based on context
        if context == "medication_start":
            # Medications: 1950 to 1 year in future (for planned starts)
            min_date = datetime(1950, 1, 1)
            max_date = now + timedelta(days=365)
        elif context == "lab_result":
            # Lab results: 1960 to 30 days in future (recent but not too far future)
            min_date = datetime(1960, 1, 1)
            max_date = now + timedelta(days=30)
        elif context == "symptom_report":
            # Symptoms: 1900 to now (historical symptoms possible, but not future)
            min_date = datetime(1900, 1, 1)
            max_date = now
        else:
            # Generic medical event: 1900 to 1 year in future
            min_date = datetime(1900, 1, 1)
            max_date = now + timedelta(days=365)
        
        return min_date <= date <= max_date


# Global instances for easy import
medical_normalizer = MedicalNormalizer()
medical_date_parser = MedicalDateParser() 