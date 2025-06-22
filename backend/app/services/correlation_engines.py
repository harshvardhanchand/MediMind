"""
Medical Correlation Engines
Comprehensive multi-domain correlation analysis for intelligent medical notifications
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from app.services.openfda_service import openfda_service
from app.utils.medical_utils import medical_normalizer, medical_date_parser

logger = logging.getLogger(__name__)

class DrugSymptomCorrelationEngine:
    """
    Analyzes correlations between medications and symptoms using FDA data + fallbacks
    Optimized with inverted indices for O(K) complexity instead of O(N×M)
    """
    
    def __init__(self):
        self.openfda_service = openfda_service
        
        # Fallback knowledge base for when FDA API is unavailable
        # Reduced to critical drugs only - FDA data takes precedence
        self.fallback_drug_effects = {
            # Critical ACE Inhibitors
            "lisinopril": {
                "dizziness": {"confidence": 0.8, "onset_days": [1, 14], "severity": "medium"},
                "dry_cough": {"confidence": 0.9, "onset_days": [7, 30], "severity": "medium"},
                "hypotension": {"confidence": 0.7, "onset_days": [1, 7], "severity": "high"}
            },
            
            # Critical Beta Blockers
            "metoprolol": {
                "fatigue": {"confidence": 0.8, "onset_days": [1, 21], "severity": "medium"},
                "dizziness": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"}
            },
            
            # Critical Diabetes Medications
            "metformin": {
                "nausea": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"},
                "diarrhea": {"confidence": 0.6, "onset_days": [1, 21], "severity": "medium"}
            }
        }
        
        # Build inverted indices for performance optimization
        self._build_inverted_indices()
    
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
                normalized_symptom = medical_normalizer.normalize_symptom_name(symptom_name)
                
                # Add to symptom → drugs mapping
                if normalized_symptom not in self.symptom_to_drugs_index:
                    self.symptom_to_drugs_index[normalized_symptom] = set()
                self.symptom_to_drugs_index[normalized_symptom].add(normalized_drug)
                
                # Add to drug → symptoms mapping
                self.drug_to_symptoms_index[normalized_drug].add(normalized_symptom)
                
                # Also add variations for better matching
                for variation in self._get_symptom_variations(symptom_name):
                    norm_variation = medical_normalizer.normalize_symptom_name(variation)
                    if norm_variation not in self.symptom_to_drugs_index:
                        self.symptom_to_drugs_index[norm_variation] = set()
                    self.symptom_to_drugs_index[norm_variation].add(normalized_drug)
    
    def _get_symptom_variations(self, symptom_name: str) -> List[str]:
        """Get common variations of a symptom name for indexing"""
        variations = [symptom_name]
        
        # Add common variations
        variation_map = {
            "dizziness": ["dizzy", "lightheaded", "light_headed", "vertigo"],
            "fatigue": ["tired", "exhausted", "weakness"],
            "nausea": ["queasy", "sick_to_stomach"],
            "dry_cough": ["cough", "persistent_cough"],
            "muscle_pain": ["muscle_ache", "myalgia", "muscle_aches"]
        }
        
        for base_symptom, vars in variation_map.items():
            if base_symptom in symptom_name.lower():
                variations.extend(vars)
        
        return variations
    
    async def analyze(self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze drug-symptom correlations using optimized indexing
        O(K) complexity where K = number of relevant matches
        """
        correlations = []
        
        try:
            # Try FDA-based correlations first (still optimized)
            fda_correlations = await self._analyze_with_fda_optimized(medications, symptoms)
            correlations.extend(fda_correlations)
            
            # Add fallback correlations using inverted indices
            fallback_correlations = await self._analyze_with_fallback_optimized(medications, symptoms, fda_correlations)
            correlations.extend(fallback_correlations)
            
        except Exception as e:
            logger.error(f"FDA analysis failed, using fallback only: {str(e)}")
            # If FDA fails, use optimized fallback
            fallback_correlations = await self._analyze_with_fallback_optimized(medications, symptoms, [])
            correlations.extend(fallback_correlations)
        
        return sorted(correlations, key=lambda x: x["confidence"], reverse=True)
    
    async def _analyze_with_fda_optimized(self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use OpenFDA service with optimized querying
        """
        correlations = []
        
        # Build medication index for faster lookups
        med_index = {}
        for med in medications:
            normalized_name = medical_normalizer.normalize_drug_name(med.get("name", ""))
            med_index[normalized_name] = med
        
        # For each symptom, check only against relevant drugs
        for symptom in symptoms:
            normalized_symptom = medical_normalizer.normalize_symptom_name(symptom.get("symptom", ""))
            
            # Get candidate drugs for this symptom from our index
            candidate_drugs = self.symptom_to_drugs_index.get(normalized_symptom, set())
            
            # Also check FDA terms for this symptom
            fda_terms = medical_normalizer.get_fda_symptom_terms(symptom.get("symptom", ""))
            for term in fda_terms:
                norm_term = medical_normalizer.normalize_symptom_name(term)
                candidate_drugs.update(self.symptom_to_drugs_index.get(norm_term, set()))
            
            # If no candidates in our index, try all medications (for unknown drugs)
            if not candidate_drugs:
                candidate_drugs = set(med_index.keys())
            
            # Query FDA only for relevant drug-symptom pairs
            for drug_name in candidate_drugs:
                if drug_name in med_index:
                    medication = med_index[drug_name]
                    fda_result = await self._query_fda_for_symptom_correlation(medication, symptom)
                    if fda_result:
                        correlations.append(fda_result)
        
        return correlations
    
    async def _analyze_with_fallback_optimized(self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]], existing_correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use fallback knowledge with inverted indices - O(K) complexity
        """
        correlations = []
        
        # Get drugs already analyzed by FDA
        fda_analyzed_drugs = set()
        for corr in existing_correlations:
            if corr.get("source") == "FDA_VALIDATED":
                fda_analyzed_drugs.add(corr.get("medication", "").lower())
        
        # Build medication index
        med_index = {}
        for med in medications:
            normalized_name = medical_normalizer.normalize_drug_name(med.get("name", ""))
            if normalized_name not in fda_analyzed_drugs:  # Skip FDA-analyzed drugs
                med_index[normalized_name] = med
        
        # For each symptom, only check against drugs that can cause it
        for symptom in symptoms:
            normalized_symptom = medical_normalizer.normalize_symptom_name(symptom.get("symptom", ""))
            
            # Get candidate drugs from inverted index
            candidate_drugs = self.symptom_to_drugs_index.get(normalized_symptom, set())
            
            # Check candidates against available medications
            for drug_name in candidate_drugs:
                if drug_name in med_index:
                    medication = med_index[drug_name]
                    correlation = self._check_fallback_correlation(medication, symptom)
                    if correlation:
                        correlations.append(correlation)
        
        return correlations
    
    async def _query_fda_for_symptom_correlation(self, medication: Dict[str, Any], symptom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                correlation = self._convert_fda_to_correlation(medication, symptom, result)
                return correlation
            
        except Exception as e:
            logger.warning(f"FDA query failed for {medication.get('name')} + {symptom.get('symptom')}: {str(e)}")
        
        return None
    
    async def _check_fda_adverse_events(self, drug_name: str, symptom_name: str) -> Optional[Dict[str, Any]]:
        """
        Direct FDA API call for drug-symptom adverse event correlation
        """
        import aiohttp
        
        try:
            url = "https://api.fda.gov/drug/event.json"
            
            # Normalize symptom name for FDA search
            symptom_search_terms = self._get_fda_symptom_terms(symptom_name)
            
            async with aiohttp.ClientSession() as session:
                for symptom_term in symptom_search_terms:
                    params = {
                        "search": f'patient.drug.medicinalproduct:"{drug_name}" AND patient.reaction.reactionmeddrapt:"{symptom_term}"',
                        "limit": 50,
                        "count": "patient.reaction.reactionmeddrapt.exact"
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("results"):
                                return self._parse_fda_symptom_data(drug_name, symptom_name, data)
                        elif response.status == 404:
                            continue  # Try next symptom term
            
        except Exception as e:
            logger.error(f"FDA API call failed: {str(e)}")
        
        return None
    
    def _get_fda_symptom_terms(self, symptom_name: str) -> List[str]:
        """
        Convert common symptom names to FDA medical terminology
        """
        return medical_normalizer.get_fda_symptom_terms(symptom_name)
    
    def _parse_fda_symptom_data(self, drug_name: str, symptom_name: str, fda_data: Dict) -> Dict[str, Any]:
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
            "data_quality": "high"
        }
    
    def _convert_fda_to_correlation(self, medication: Dict[str, Any], symptom: Dict[str, Any], fda_result: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Calculate timing score if dates available
        timing_score = self._calculate_timing_score(medication, symptom, {"onset_days": [1, 30]})
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
                "expected_onset_days": [1, 30]  # Conservative estimate
            },
            "recommendation": self._generate_fda_based_recommendation(medication, symptom, severity, total_reports)
        }
    
    def _generate_fda_based_recommendation(self, medication: Dict[str, Any], symptom: Dict[str, Any], severity: str, report_count: int) -> str:
        """
        Generate FDA-based recommendation
        """
        med_name = medication.get("name")
        symptom_name = symptom.get("symptom")
        
        if severity == "high" or report_count > 500:
            return f"⚠️ FDA data shows {symptom_name} is frequently reported with {med_name} ({report_count} reports). Contact your doctor immediately."
        elif severity == "medium" or report_count > 100:
            return f"📊 FDA adverse event reports link {symptom_name} to {med_name} ({report_count} reports). Discuss with your healthcare provider."
        else:
            return f"📝 FDA has {report_count} reports of {symptom_name} with {med_name}. Mention this to your doctor at your next visit."
    
    def _check_fallback_correlation(self, medication: Dict[str, Any], symptom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
        timing_score = self._calculate_timing_score(medication, symptom, matching_effect)
        base_confidence = matching_effect["confidence"]
        final_confidence = base_confidence * timing_score * 0.9  # Slightly lower confidence for fallback
        
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
                "expected_onset_days": matching_effect["onset_days"]
            },
            "recommendation": self._generate_drug_symptom_recommendation(medication, symptom, matching_effect)
        }
    
    def _calculate_timing_score(self, medication: Dict[str, Any], symptom: Dict[str, Any], effect_data: Dict[str, Any]) -> float:
        """Calculate timing correlation score using robust date parsing"""
        try:
            med_start = medication.get("start_date")
            symptom_date = symptom.get("reported_date") or symptom.get("date")
            
            if not med_start or not symptom_date:
                return 0.8  # Default score when timing data unavailable
            
            # Use robust date parsing with appropriate context
            med_start_dt = medical_date_parser.parse_medical_date(med_start, "medication_start")
            symptom_date_dt = medical_date_parser.parse_medical_date(symptom_date, "symptom_report")
            
            if not med_start_dt or not symptom_date_dt:
                # Don't default to now() - return lower confidence instead
                logger.warning(f"Could not parse dates for timing analysis: med_start={med_start}, symptom_date={symptom_date}")
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
    
    def _generate_drug_symptom_recommendation(self, medication: Dict[str, Any], symptom: Dict[str, Any], effect_data: Dict[str, Any]) -> str:
        """Generate actionable recommendation"""
        severity = effect_data["severity"]
        med_name = medication.get("name")
        symptom_name = symptom.get("symptom")
        
        if severity == "high":
            return f"⚠️ {symptom_name} may be a serious side effect of {med_name}. Contact your doctor immediately."
        elif severity == "medium":
            return f"💊 {symptom_name} is a known side effect of {med_name}. Monitor and discuss with your healthcare provider."
        else:
            return f"📝 {symptom_name} could be related to {med_name}. Mention this to your doctor at your next visit."


class LabSymptomCorrelationEngine:
    """
    Analyzes correlations between lab results and symptoms
    Optimized with inverted indices for O(K) complexity
    """
    
    def __init__(self):
        # Medical knowledge base for lab-symptom correlations
        self.lab_symptom_patterns = {
            # Blood Sugar
            "glucose": {
                "high_patterns": {
                    "frequent_urination": {"threshold": ">180", "confidence": 0.9},
                    "excessive_thirst": {"threshold": ">180", "confidence": 0.9},
                    "fatigue": {"threshold": ">250", "confidence": 0.7},
                    "blurred_vision": {"threshold": ">200", "confidence": 0.6}
                },
                "low_patterns": {
                    "dizziness": {"threshold": "<70", "confidence": 0.8},
                    "shakiness": {"threshold": "<70", "confidence": 0.9},
                    "sweating": {"threshold": "<60", "confidence": 0.8},
                    "confusion": {"threshold": "<50", "confidence": 0.9}
                }
            },
            
            # Hemoglobin/Anemia
            "hemoglobin": {
                "low_patterns": {
                    "fatigue": {"threshold": "<12", "confidence": 0.9},
                    "weakness": {"threshold": "<11", "confidence": 0.8},
                    "shortness_of_breath": {"threshold": "<10", "confidence": 0.8},
                    "pale_skin": {"threshold": "<11", "confidence": 0.7},
                    "cold_hands": {"threshold": "<10", "confidence": 0.6}
                }
            },
            
            # Thyroid
            "tsh": {
                "high_patterns": {  # Hypothyroidism
                    "fatigue": {"threshold": ">4.5", "confidence": 0.8},
                    "weight_gain": {"threshold": ">5", "confidence": 0.7},
                    "cold_intolerance": {"threshold": ">4.5", "confidence": 0.6},
                    "constipation": {"threshold": ">5", "confidence": 0.6}
                },
                "low_patterns": {  # Hyperthyroidism
                    "weight_loss": {"threshold": "<0.4", "confidence": 0.7},
                    "heart_palpitations": {"threshold": "<0.3", "confidence": 0.8},
                    "anxiety": {"threshold": "<0.4", "confidence": 0.6},
                    "sweating": {"threshold": "<0.3", "confidence": 0.7}
                }
            },
            
            # Kidney Function
            "creatinine": {
                "high_patterns": {
                    "swelling": {"threshold": ">1.5", "confidence": 0.8},
                    "fatigue": {"threshold": ">2.0", "confidence": 0.7},
                    "nausea": {"threshold": ">2.5", "confidence": 0.6},
                    "decreased_urination": {"threshold": ">2.0", "confidence": 0.7}
                }
            },
            
            # Liver Function
            "alt": {
                "high_patterns": {
                    "fatigue": {"threshold": ">80", "confidence": 0.6},
                    "nausea": {"threshold": ">100", "confidence": 0.7},
                    "abdominal_pain": {"threshold": ">120", "confidence": 0.6}
                }
            }
        }
        
        # Build inverted indices for performance optimization
        self._build_symptom_lab_indices()
    
    def _build_symptom_lab_indices(self):
        """
        Build inverted indices: symptom → [lab_tests that could explain it]
        Optimizes from O(N×M) to O(K) where K = relevant matches
        """
        self.symptom_to_labs_index = {}
        self.lab_to_symptoms_index = {}
        
        for lab_test, patterns in self.lab_symptom_patterns.items():
            normalized_lab = lab_test.lower().strip()
            self.lab_to_symptoms_index[normalized_lab] = set()
            
            for pattern_type, symptoms in patterns.items():
                for symptom_name, pattern_data in symptoms.items():
                    normalized_symptom = medical_normalizer.normalize_symptom_name(symptom_name)
                    
                    # Add to symptom → labs mapping
                    if normalized_symptom not in self.symptom_to_labs_index:
                        self.symptom_to_labs_index[normalized_symptom] = set()
                    self.symptom_to_labs_index[normalized_symptom].add(normalized_lab)
                    
                    # Add to lab → symptoms mapping
                    self.lab_to_symptoms_index[normalized_lab].add(normalized_symptom)
                    
                    # Add symptom variations for better matching
                    for variation in self._get_symptom_variations(symptom_name):
                        norm_variation = medical_normalizer.normalize_symptom_name(variation)
                        if norm_variation not in self.symptom_to_labs_index:
                            self.symptom_to_labs_index[norm_variation] = set()
                        self.symptom_to_labs_index[norm_variation].add(normalized_lab)
    
    def _get_symptom_variations(self, symptom_name: str) -> List[str]:
        """Get common variations of a symptom name for lab correlation indexing"""
        variations = [symptom_name]
        
        # Lab-specific symptom variations
        variation_map = {
            "fatigue": ["tired", "exhausted", "weakness", "low_energy"],
            "shortness_of_breath": ["breathless", "short_of_breath", "difficulty_breathing"],
            "frequent_urination": ["frequent_urinating", "polyuria"],
            "excessive_thirst": ["increased_thirst", "polydipsia"],
            "weight_loss": ["losing_weight", "weight_drop"],
            "weight_gain": ["gaining_weight", "weight_increase"],
            "heart_palpitations": ["palpitations", "rapid_heartbeat", "racing_heart"],
            "abdominal_pain": ["stomach_pain", "belly_pain", "stomach_ache"]
        }
        
        for base_symptom, vars in variation_map.items():
            if base_symptom in symptom_name.lower():
                variations.extend(vars)
        
        return variations
    
    def analyze(self, lab_results: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze lab-symptom correlations using optimized indexing
        O(K) complexity where K = number of relevant matches
        """
        correlations = []
        
        # Build lab results index for faster lookups
        lab_index = {}
        for lab in lab_results:
            test_name = lab.get("test", "").lower().strip()
            if test_name not in lab_index:
                lab_index[test_name] = []
            lab_index[test_name].append(lab)
        
        # For each symptom, only check against relevant lab tests
        for symptom in symptoms:
            normalized_symptom = medical_normalizer.normalize_symptom_name(symptom.get("symptom", ""))
            
            # Get candidate lab tests from inverted index
            candidate_labs = self.symptom_to_labs_index.get(normalized_symptom, set())
            
            # Check candidates against available lab results
            for lab_test in candidate_labs:
                if lab_test in lab_index:
                    for lab_result in lab_index[lab_test]:
                        correlation = self._check_lab_symptom_correlation(lab_result, symptom)
                        if correlation:
                            correlations.append(correlation)
        
        return sorted(correlations, key=lambda x: x["confidence"], reverse=True)
    
    def _check_lab_symptom_correlation(self, lab_result: Dict[str, Any], symptom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if lab result explains symptom
        """
        test_name = lab_result.get("test", "").lower().strip()
        symptom_name = symptom.get("symptom", "").lower().strip()
        lab_value = lab_result.get("value")
        
        if not lab_value or test_name not in self.lab_symptom_patterns:
            return None
        
        test_patterns = self.lab_symptom_patterns[test_name]
        
        # Check high and low patterns
        for pattern_type, patterns in test_patterns.items():
            if symptom_name in patterns:
                pattern_data = patterns[symptom_name]
                if self._value_meets_threshold(lab_value, pattern_data["threshold"]):
                    return {
                        "type": "lab_symptom_correlation",
                        "lab_test": lab_result.get("test"),
                        "lab_value": lab_value,
                        "symptom": symptom.get("symptom"),
                        "confidence": pattern_data["confidence"],
                        "pattern_type": pattern_type,
                        "threshold": pattern_data["threshold"],
                        "mechanism": self._get_physiological_mechanism(test_name, symptom_name, pattern_type),
                        "recommendation": self._generate_lab_symptom_recommendation(lab_result, symptom, pattern_type)
                    }
        
        return None
    
    def _value_meets_threshold(self, value: float, threshold: str) -> bool:
        """Check if lab value meets threshold criteria"""
        try:
            if threshold.startswith(">"):
                threshold_val = float(threshold[1:])
                return value > threshold_val
            elif threshold.startswith("<"):
                threshold_val = float(threshold[1:])
                return value < threshold_val
            elif threshold.startswith(">="):
                threshold_val = float(threshold[2:])
                return value >= threshold_val
            elif threshold.startswith("<="):
                threshold_val = float(threshold[2:])
                return value <= threshold_val
        except (ValueError, TypeError):
            return False
        
        return False
    
    def _get_physiological_mechanism(self, test_name: str, symptom_name: str, pattern_type: str) -> str:
        """Explain the physiological mechanism"""
        mechanisms = {
            ("glucose", "frequent_urination", "high_patterns"): "High blood sugar causes kidneys to produce more urine to eliminate excess glucose",
            ("hemoglobin", "fatigue", "low_patterns"): "Low hemoglobin reduces oxygen delivery to tissues, causing fatigue",
            ("tsh", "weight_gain", "high_patterns"): "High TSH indicates underactive thyroid, which slows metabolism",
            ("creatinine", "swelling", "high_patterns"): "High creatinine indicates kidney dysfunction, leading to fluid retention"
        }
        
        return mechanisms.get((test_name, symptom_name, pattern_type), f"Abnormal {test_name} level may contribute to {symptom_name}")
    
    def _generate_lab_symptom_recommendation(self, lab_result: Dict[str, Any], symptom: Dict[str, Any], pattern_type: str) -> str:
        """Generate actionable recommendation"""
        test_name = lab_result.get("test")
        symptom_name = symptom.get("symptom")
        value = lab_result.get("value")
        
        if "high" in pattern_type:
            return f"🔬 Your {symptom_name} may be related to elevated {test_name} ({value}). Discuss treatment options with your doctor."
        else:
            return f"🔬 Your {symptom_name} may be related to low {test_name} ({value}). Consider discussing supplementation or treatment with your healthcare provider."


class DrugLabCorrelationEngine:
    """
    Analyzes correlations between medications and lab results
    Optimized with inverted indices for O(K) complexity
    """
    
    def __init__(self):
        # Drug-lab monitoring patterns
        self.drug_lab_monitoring = {
            "metformin": {
                "b12": {"effect": "decreases", "monitoring": "annual", "concern_threshold": "<300"},
                "creatinine": {"effect": "monitor", "monitoring": "every_6_months", "concern_threshold": ">1.5"}
            },
            "warfarin": {
                "inr": {"effect": "increases", "monitoring": "weekly_initially", "target_range": "2.0-3.0"},
                "pt": {"effect": "increases", "monitoring": "with_inr", "concern_threshold": ">35"}
            },
            "atorvastatin": {
                "alt": {"effect": "increases", "monitoring": "baseline_then_periodic", "concern_threshold": ">80"},
                "ast": {"effect": "increases", "monitoring": "baseline_then_periodic", "concern_threshold": ">80"},
                "cpk": {"effect": "increases", "monitoring": "if_symptoms", "concern_threshold": ">300"}
            },
            "lisinopril": {
                "creatinine": {"effect": "may_increase", "monitoring": "baseline_then_periodic", "concern_threshold": ">1.5"},
                "potassium": {"effect": "increases", "monitoring": "baseline_then_periodic", "concern_threshold": ">5.0"}
            }
        }
        
        # Build inverted indices for performance optimization
        self._build_drug_lab_indices()
    
    def _build_drug_lab_indices(self):
        """
        Build inverted indices: drug → [lab_tests to monitor], lab_test → [drugs that affect it]
        Optimizes from O(N×M) to O(K) where K = relevant matches
        """
        self.drug_to_labs_index = {}
        self.lab_to_drugs_index = {}
        
        for drug_name, lab_tests in self.drug_lab_monitoring.items():
            normalized_drug = medical_normalizer.normalize_drug_name(drug_name)
            self.drug_to_labs_index[normalized_drug] = set()
            
            for lab_test, monitoring_data in lab_tests.items():
                normalized_lab = lab_test.lower().strip()
                
                # Add to drug → labs mapping
                self.drug_to_labs_index[normalized_drug].add(normalized_lab)
                
                # Add to lab → drugs mapping
                if normalized_lab not in self.lab_to_drugs_index:
                    self.lab_to_drugs_index[normalized_lab] = set()
                self.lab_to_drugs_index[normalized_lab].add(normalized_drug)
                
                # Add drug name variations
                for variation in self._get_drug_variations(drug_name):
                    norm_variation = medical_normalizer.normalize_drug_name(variation)
                    if norm_variation not in self.drug_to_labs_index:
                        self.drug_to_labs_index[norm_variation] = set()
                    self.drug_to_labs_index[norm_variation].add(normalized_lab)
                    self.lab_to_drugs_index[normalized_lab].add(norm_variation)
    
    def _get_drug_variations(self, drug_name: str) -> List[str]:
        """Get common brand/generic variations of drug names"""
        variations = [drug_name]
        
        # Common brand/generic mappings
        brand_generic_map = {
            "metformin": ["glucophage", "fortamet", "riomet"],
            "atorvastatin": ["lipitor"],
            "lisinopril": ["zestril", "prinivil"],
            "warfarin": ["coumadin", "jantoven"]
        }
        
        for generic, brands in brand_generic_map.items():
            if generic in drug_name.lower():
                variations.extend(brands)
            elif drug_name.lower() in brands:
                variations.append(generic)
        
        return variations
    
    def analyze(self, medications: List[Dict[str, Any]], lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze drug-lab correlations using optimized indexing
        O(K) complexity where K = number of relevant matches
        """
        correlations = []
        
        # Build indices for faster lookups
        med_index = {}
        for med in medications:
            normalized_name = medical_normalizer.normalize_drug_name(med.get("name", ""))
            if normalized_name not in med_index:
                med_index[normalized_name] = []
            med_index[normalized_name].append(med)
        
        lab_index = {}
        for lab in lab_results:
            test_name = lab.get("test", "").lower().strip()
            if test_name not in lab_index:
                lab_index[test_name] = []
            lab_index[test_name].append(lab)
        
        # Approach 1: For each drug, check its relevant lab tests
        for drug_name, drug_list in med_index.items():
            relevant_labs = self.drug_to_labs_index.get(drug_name, set())
            
            for lab_test in relevant_labs:
                if lab_test in lab_index:
                    for medication in drug_list:
                        for lab_result in lab_index[lab_test]:
                            correlation = self._check_drug_lab_correlation(medication, lab_result)
                            if correlation:
                                correlations.append(correlation)
        
        return sorted(correlations, key=lambda x: x.get("urgency_score", 0), reverse=True)
    
    def _check_drug_lab_correlation(self, medication: Dict[str, Any], lab_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if medication affects lab result
        """
        drug_name = medication.get("name", "").lower().strip()
        test_name = lab_result.get("test", "").lower().strip()
        
        # Normalize names using centralized utilities
        drug_name = medical_normalizer.normalize_drug_name(drug_name)
        
        if drug_name not in self.drug_lab_monitoring:
            return None
        
        drug_patterns = self.drug_lab_monitoring[drug_name]
        
        if test_name not in drug_patterns:
            return None
        
        pattern_data = drug_patterns[test_name]
        lab_value = lab_result.get("value")
        
        # Check if lab value indicates concern
        concern_level = self._assess_concern_level(lab_value, pattern_data)
        
        if concern_level == "none":
            return None  # No concerning values
        
        return {
            "type": "drug_lab_correlation",
            "medication": medication.get("name"),
            "lab_test": lab_result.get("test"),
            "lab_value": lab_value,
            "effect_type": pattern_data["effect"],
            "concern_level": concern_level,
            "monitoring_recommendation": pattern_data["monitoring"],
            "urgency_score": self._calculate_urgency_score(concern_level, pattern_data),
            "recommendation": self._generate_drug_lab_recommendation(medication, lab_result, pattern_data, concern_level)
        }
    

    
    def _assess_concern_level(self, lab_value: float, pattern_data: Dict[str, Any]) -> str:
        """Assess level of concern based on lab value"""
        if not lab_value:
            return "none"
        
        concern_threshold = pattern_data.get("concern_threshold")
        target_range = pattern_data.get("target_range")
        
        if concern_threshold:
            if self._value_meets_threshold(lab_value, concern_threshold):
                return "high"
        
        if target_range:
            if not self._value_in_range(lab_value, target_range):
                return "medium"
        
        return "monitor"  # Value to monitor but not immediately concerning
    
    def _value_meets_threshold(self, value: float, threshold: str) -> bool:
        """Check if value meets threshold"""
        try:
            if threshold.startswith(">"):
                return value > float(threshold[1:])
            elif threshold.startswith("<"):
                return value < float(threshold[1:])
        except (ValueError, TypeError):
            return False
        return False
    
    def _value_in_range(self, value: float, range_str: str) -> bool:
        """Check if value is in target range"""
        try:
            # Parse range like "2.0-3.0"
            min_val, max_val = map(float, range_str.split("-"))
            return min_val <= value <= max_val
        except (ValueError, TypeError):
            return True
    
    def _calculate_urgency_score(self, concern_level: str, pattern_data: Dict[str, Any]) -> float:
        """Calculate urgency score for prioritization"""
        base_scores = {"high": 0.9, "medium": 0.6, "monitor": 0.3, "none": 0.0}
        return base_scores.get(concern_level, 0.0)
    
    def _generate_drug_lab_recommendation(self, medication: Dict[str, Any], lab_result: Dict[str, Any], pattern_data: Dict[str, Any], concern_level: str) -> str:
        """Generate recommendation for drug-lab correlation"""
        med_name = medication.get("name")
        test_name = lab_result.get("test")
        value = lab_result.get("value")
        
        if concern_level == "high":
            return f"⚠️ {test_name} level ({value}) may be affected by {med_name}. Urgent consultation with healthcare provider recommended."
        elif concern_level == "medium":
            return f"📊 {test_name} level ({value}) should be monitored while taking {med_name}. Discuss with your doctor."
        else:
            return f"📋 Continue monitoring {test_name} levels as recommended while taking {med_name}."


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
    
    def _create_unified_timeline(self, medical_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create unified timeline of all medical events"""
        timeline = []
        
        # Add medications
        for med in medical_profile.get("medications", []):
            if med.get("start_date"):
                parsed_date = self._parse_date(med["start_date"])
                if parsed_date:  # Only add if date is valid
                    timeline.append({
                        "date": med["start_date"],
                        "parsed_date": parsed_date,
                        "type": "medication_started",
                        "data": med,
                        "entity": "medication"
                    })
        
        # Add symptoms
        for symptom in medical_profile.get("recent_symptoms", []):
            symptom_date = symptom.get("reported_date") or symptom.get("date")
            if symptom_date:
                parsed_date = self._parse_date(symptom_date)
                if parsed_date:  # Only add if date is valid
                    timeline.append({
                        "date": symptom_date,
                        "parsed_date": parsed_date,
                        "type": "symptom_reported",
                        "data": symptom,
                        "entity": "symptom"
                    })
        
        # Add lab results
        for lab in medical_profile.get("lab_results", []):
            if lab.get("date"):
                parsed_date = self._parse_date(lab["date"])
                if parsed_date:  # Only add if date is valid
                    timeline.append({
                        "date": lab["date"],
                        "parsed_date": parsed_date,
                        "type": "lab_result",
                        "data": lab,
                        "entity": "lab"
                    })
        
        # Sort by parsed date
        timeline.sort(key=lambda x: x["parsed_date"])
        
        return timeline
    
    def _find_event_clusters(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                clusters.append({
                    "type": "temporal_cluster",
                    "events": cluster_events,
                    "timeframe_days": window_days,
                    "confidence": min(0.9, len(cluster_events) * 0.3),
                    "pattern_description": f"{len(cluster_events)} medical events within {window_days} days",
                    "recommendation": self._generate_cluster_recommendation(cluster_events)
                })
        
        return clusters
    
    def _find_sequential_patterns(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                        
                        if 1 <= days_diff <= 30:  # Reasonable timeframe for side effects
                            patterns.append({
                                "type": "medication_symptom_sequence",
                                "medication": event["data"],
                                "symptom": next_event["data"],
                                "days_between": days_diff,
                                "confidence": 0.7,
                                "pattern_description": f"Symptom appeared {days_diff} days after starting medication",
                                "recommendation": f"Consider if {next_event['data'].get('symptom')} could be related to {event['data'].get('name')}"
                            })
        
        return patterns
    
    def _generate_cluster_recommendation(self, cluster_events: List[Dict[str, Any]]) -> str:
        """Generate recommendation for event cluster"""
        event_types = [event["type"] for event in cluster_events]
        
        if "medication_started" in event_types and "symptom_reported" in event_types:
            return "🔍 Multiple medical events occurred close together. Consider if new symptoms could be related to medication changes."
        elif "lab_result" in event_types and "symptom_reported" in event_types:
            return "📊 Lab results and symptoms occurred close together. Review if lab abnormalities explain symptoms."
        else:
            return f"📅 {len(cluster_events)} medical events occurred within a short timeframe. Consider reviewing for connections."


class MultiCorrelationAnalyzer:
    """
    Master orchestrator for multi-domain correlation analysis
    """
    
    def __init__(self):
        self.drug_symptom_engine = DrugSymptomCorrelationEngine()
        self.lab_symptom_engine = LabSymptomCorrelationEngine()
        self.drug_lab_engine = DrugLabCorrelationEngine()
        self.temporal_engine = TemporalPatternEngine()
    
    async def analyze_comprehensive_correlations(self, medical_profile: Dict[str, Any], trigger_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive multi-domain correlation analysis
        """
        logger.info(f"Starting comprehensive correlation analysis for trigger: {trigger_event.get('type')}")
        
        # Run all correlation engines (drug_symptom is now async)
        correlations = {
            "drug_symptom": await self.drug_symptom_engine.analyze(
                medical_profile.get("medications", []), 
                medical_profile.get("recent_symptoms", [])
            ),
            "lab_symptom": self.lab_symptom_engine.analyze(
                medical_profile.get("lab_results", []), 
                medical_profile.get("recent_symptoms", [])
            ),
            "drug_lab": self.drug_lab_engine.analyze(
                medical_profile.get("medications", []), 
                medical_profile.get("lab_results", [])
            ),
            "temporal_patterns": self.temporal_engine.analyze(medical_profile)
        }
        
        # Cross-validate and prioritize correlations
        validated_correlations = self._cross_validate_correlations(correlations, trigger_event)
        prioritized_correlations = self._prioritize_correlations(validated_correlations, trigger_event)
        
        # Generate comprehensive insights
        insights = self._generate_comprehensive_insights(prioritized_correlations, trigger_event)
        
        logger.info(f"Correlation analysis complete: {len(prioritized_correlations)} correlations found")
        
        return {
            "correlations": prioritized_correlations,
            "insights": insights,
            "trigger_event": trigger_event,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _cross_validate_correlations(self, correlations: Dict[str, List], trigger_event: Dict[str, Any]) -> List[Dict[str, Any]]:
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
            supporting_evidence = self._find_supporting_evidence(correlation, all_correlations)
            
            if supporting_evidence:
                correlation["supporting_evidence"] = supporting_evidence
                correlation["confidence"] = min(0.95, correlation["confidence"] * 1.2)  # Boost confidence
            
            reinforced_correlations.append(correlation)
        
        return reinforced_correlations
    
    def _find_supporting_evidence(self, target_correlation: Dict[str, Any], all_correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find correlations that support the target correlation"""
        supporting = []
        
        for correlation in all_correlations:
            if correlation == target_correlation:
                continue
            
            # Check for overlapping entities
            if self._correlations_overlap(target_correlation, correlation):
                supporting.append({
                    "engine": correlation["engine"],
                    "type": correlation["type"],
                    "confidence": correlation["confidence"]
                })
        
        return supporting
    
    def _correlations_overlap(self, corr1: Dict[str, Any], corr2: Dict[str, Any]) -> bool:
        """Check if two correlations involve overlapping entities"""
        # Extract entities from correlations
        entities1 = set()
        entities2 = set()
        
        for key in ["medication", "symptom", "lab_test"]:
            if corr1.get(key):
                entities1.add(corr1[key].lower())
            if corr2.get(key):
                entities2.add(corr2[key].lower())
        
        return bool(entities1.intersection(entities2))
    
    def _prioritize_correlations(self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize correlations based on multiple factors"""
        
        for correlation in correlations:
            priority_score = self._calculate_priority_score(correlation, trigger_event)
            correlation["priority_score"] = priority_score
        
        return sorted(correlations, key=lambda x: x["priority_score"], reverse=True)
    
    def _calculate_priority_score(self, correlation: Dict[str, Any], trigger_event: Dict[str, Any]) -> float:
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
    
    def _calculate_trigger_relevance(self, correlation: Dict[str, Any], trigger_event: Dict[str, Any]) -> float:
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
    
    def _generate_comprehensive_insights(self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive insights from all correlations"""
        
        # Take top correlations for insights
        top_correlations = correlations[:5]
        
        insights = {
            "summary": self._generate_summary_insight(top_correlations, trigger_event),
            "recommendations": self._generate_actionable_recommendations(top_correlations),
            "risk_alerts": self._generate_risk_alerts(top_correlations),
            "monitoring_suggestions": self._generate_monitoring_suggestions(top_correlations)
        }
        
        return insights
    
    def _generate_summary_insight(self, correlations: List[Dict[str, Any]], trigger_event: Dict[str, Any]) -> str:
        """Generate summary insight"""
        if not correlations:
            return f"No significant correlations found for {trigger_event.get('type', 'this event')}."
        
        high_priority = [c for c in correlations if c.get("priority_score", 0) > 0.8]
        
        if high_priority:
            return f"Found {len(high_priority)} high-priority medical correlations that may require attention."
        else:
            return f"Found {len(correlations)} potential medical correlations worth monitoring."
    
    def _generate_actionable_recommendations(self, correlations: List[Dict[str, Any]]) -> List[str]:
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
            if (correlation.get("severity") == "high" or 
                correlation.get("concern_level") == "high" or 
                correlation.get("priority_score", 0) > 0.85):
                
                alert = f"HIGH RISK: {correlation.get('type', 'Medical correlation')} detected"
                if correlation.get("medication"):
                    alert += f" involving {correlation['medication']}"
                alerts.append(alert)
        
        return alerts
    
    def _generate_monitoring_suggestions(self, correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate monitoring suggestions"""
        suggestions = []
        
        monitoring_items = set()
        for correlation in correlations:
            if correlation.get("monitoring_recommendation"):
                monitoring_items.add(correlation["monitoring_recommendation"])
        
        return list(monitoring_items)


# Global instance
multi_correlation_analyzer = MultiCorrelationAnalyzer() 