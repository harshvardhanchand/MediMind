"""
Medical Correlation Engines
Comprehensive multi-domain correlation analysis for intelligent medical notifications
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DrugSymptomCorrelationEngine:
    """
    Analyzes correlations between medications and symptoms
    """
    
    def __init__(self):
        # Medical knowledge base for drug-symptom correlations
        self.drug_side_effects = {
            # ACE Inhibitors
            "lisinopril": {
                "dizziness": {"confidence": 0.8, "onset_days": [1, 14], "severity": "medium"},
                "dry_cough": {"confidence": 0.9, "onset_days": [7, 30], "severity": "medium"},
                "hypotension": {"confidence": 0.7, "onset_days": [1, 7], "severity": "high"},
                "fatigue": {"confidence": 0.6, "onset_days": [1, 14], "severity": "low"}
            },
            
            # Beta Blockers
            "metoprolol": {
                "fatigue": {"confidence": 0.8, "onset_days": [1, 21], "severity": "medium"},
                "dizziness": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"},
                "depression": {"confidence": 0.5, "onset_days": [14, 60], "severity": "medium"},
                "cold_hands": {"confidence": 0.6, "onset_days": [1, 7], "severity": "low"}
            },
            
            # Diabetes Medications
            "metformin": {
                "nausea": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"},
                "diarrhea": {"confidence": 0.6, "onset_days": [1, 21], "severity": "medium"},
                "metallic_taste": {"confidence": 0.5, "onset_days": [1, 7], "severity": "low"},
                "stomach_upset": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"}
            },
            
            # Statins
            "atorvastatin": {
                "muscle_pain": {"confidence": 0.8, "onset_days": [7, 60], "severity": "medium"},
                "muscle_weakness": {"confidence": 0.6, "onset_days": [14, 90], "severity": "high"},
                "headache": {"confidence": 0.5, "onset_days": [1, 14], "severity": "low"},
                "liver_problems": {"confidence": 0.3, "onset_days": [30, 180], "severity": "high"}
            },
            
            # Blood Thinners
            "warfarin": {
                "bleeding": {"confidence": 0.9, "onset_days": [1, 7], "severity": "high"},
                "bruising": {"confidence": 0.8, "onset_days": [1, 14], "severity": "medium"},
                "nosebleeds": {"confidence": 0.7, "onset_days": [1, 21], "severity": "medium"}
            },
            
            # Antibiotics
            "amoxicillin": {
                "nausea": {"confidence": 0.6, "onset_days": [1, 7], "severity": "medium"},
                "diarrhea": {"confidence": 0.7, "onset_days": [1, 14], "severity": "medium"},
                "rash": {"confidence": 0.4, "onset_days": [1, 10], "severity": "medium"},
                "stomach_upset": {"confidence": 0.6, "onset_days": [1, 7], "severity": "medium"}
            }
        }
    
    def analyze(self, medications: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze drug-symptom correlations
        """
        correlations = []
        
        for med in medications:
            for symptom in symptoms:
                correlation = self._check_drug_symptom_correlation(med, symptom)
                if correlation:
                    correlations.append(correlation)
        
        return sorted(correlations, key=lambda x: x["confidence"], reverse=True)
    
    def _check_drug_symptom_correlation(self, medication: Dict[str, Any], symptom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if a specific medication could cause a specific symptom
        """
        drug_name = medication.get("name", "").lower().strip()
        symptom_name = symptom.get("symptom", "").lower().strip()
        
        # Normalize drug names (remove common suffixes)
        drug_name = self._normalize_drug_name(drug_name)
        symptom_name = self._normalize_symptom_name(symptom_name)
        
        if drug_name not in self.drug_side_effects:
            return None
        
        drug_effects = self.drug_side_effects[drug_name]
        
        # Check for direct match or similar symptoms
        matching_effect = None
        for effect_name, effect_data in drug_effects.items():
            if self._symptoms_match(symptom_name, effect_name):
                matching_effect = effect_data
                break
        
        if not matching_effect:
            return None
        
        # Check timing if available
        timing_score = self._calculate_timing_score(medication, symptom, matching_effect)
        
        # Calculate final confidence
        base_confidence = matching_effect["confidence"]
        final_confidence = base_confidence * timing_score
        
        if final_confidence < 0.5:  # Threshold for reporting
            return None
        
        return {
            "type": "drug_symptom_correlation",
            "medication": medication.get("name"),
            "symptom": symptom.get("symptom"),
            "confidence": final_confidence,
            "severity": matching_effect["severity"],
            "timing_analysis": {
                "timing_score": timing_score,
                "expected_onset_days": matching_effect["onset_days"]
            },
            "recommendation": self._generate_drug_symptom_recommendation(medication, symptom, matching_effect)
        }
    
    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name for matching"""
        # Remove common suffixes and brand name variations
        suffixes = ["er", "xl", "cr", "sr", "mg", "mcg"]
        normalized = drug_name.lower()
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        return normalized
    
    def _normalize_symptom_name(self, symptom_name: str) -> str:
        """Normalize symptom name for matching"""
        # Handle common symptom variations
        symptom_mapping = {
            "tired": "fatigue",
            "exhausted": "fatigue",
            "lightheaded": "dizziness",
            "light_headed": "dizziness",
            "upset_stomach": "stomach_upset",
            "stomach_pain": "stomach_upset",
            "muscle_ache": "muscle_pain",
            "muscle_aches": "muscle_pain"
        }
        
        normalized = symptom_name.lower().replace(" ", "_")
        return symptom_mapping.get(normalized, normalized)
    
    def _symptoms_match(self, reported_symptom: str, known_effect: str) -> bool:
        """Check if reported symptom matches known drug effect"""
        # Direct match
        if reported_symptom == known_effect:
            return True
        
        # Partial matches for common variations
        partial_matches = [
            ("muscle", "muscle"),
            ("stomach", "stomach"),
            ("nausea", "nausea"),
            ("dizz", "dizz"),  # dizziness variations
            ("fatigue", "tired"),
            ("tired", "fatigue")
        ]
        
        for pattern1, pattern2 in partial_matches:
            if pattern1 in reported_symptom and pattern2 in known_effect:
                return True
            if pattern2 in reported_symptom and pattern1 in known_effect:
                return True
        
        return False
    
    def _calculate_timing_score(self, medication: Dict[str, Any], symptom: Dict[str, Any], effect_data: Dict[str, Any]) -> float:
        """Calculate timing correlation score"""
        try:
            med_start = medication.get("start_date")
            symptom_date = symptom.get("reported_date") or symptom.get("date")
            
            if not med_start or not symptom_date:
                return 0.8  # Default score when timing data unavailable
            
            # Parse dates
            if isinstance(med_start, str):
                med_start = datetime.fromisoformat(med_start.replace("Z", "+00:00"))
            if isinstance(symptom_date, str):
                symptom_date = datetime.fromisoformat(symptom_date.replace("Z", "+00:00"))
            
            days_diff = (symptom_date - med_start).days
            
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
            return 0.8  # Default score on error
        
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
    
    def analyze(self, lab_results: List[Dict[str, Any]], symptoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze lab-symptom correlations
        """
        correlations = []
        
        for lab in lab_results:
            for symptom in symptoms:
                correlation = self._check_lab_symptom_correlation(lab, symptom)
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
    
    def analyze(self, medications: List[Dict[str, Any]], lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze drug-lab correlations
        """
        correlations = []
        
        for med in medications:
            for lab in lab_results:
                correlation = self._check_drug_lab_correlation(med, lab)
                if correlation:
                    correlations.append(correlation)
        
        return sorted(correlations, key=lambda x: x.get("urgency_score", 0), reverse=True)
    
    def _check_drug_lab_correlation(self, medication: Dict[str, Any], lab_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if medication affects lab result
        """
        drug_name = medication.get("name", "").lower().strip()
        test_name = lab_result.get("test", "").lower().strip()
        
        # Normalize names
        drug_name = self._normalize_drug_name(drug_name)
        
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
    
    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name for matching"""
        # Remove dosage information and common suffixes
        import re
        normalized = re.sub(r'\d+\s*mg', '', drug_name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
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
    
    def _create_unified_timeline(self, medical_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create unified timeline of all medical events"""
        timeline = []
        
        # Add medications
        for med in medical_profile.get("medications", []):
            if med.get("start_date"):
                timeline.append({
                    "date": med["start_date"],
                    "type": "medication_started",
                    "data": med,
                    "entity": "medication"
                })
        
        # Add symptoms
        for symptom in medical_profile.get("recent_symptoms", []):
            if symptom.get("reported_date") or symptom.get("date"):
                timeline.append({
                    "date": symptom.get("reported_date") or symptom.get("date"),
                    "type": "symptom_reported",
                    "data": symptom,
                    "entity": "symptom"
                })
        
        # Add lab results
        for lab in medical_profile.get("lab_results", []):
            if lab.get("date"):
                timeline.append({
                    "date": lab["date"],
                    "type": "lab_result",
                    "data": lab,
                    "entity": "lab"
                })
        
        # Sort by date
        timeline.sort(key=lambda x: self._parse_date(x["date"]))
        
        return timeline
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date_str
        except:
            return datetime.now()
    
    def _find_event_clusters(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find clusters of events in short timeframes"""
        clusters = []
        window_days = 7  # Look for events within 7 days
        
        for i, event in enumerate(timeline):
            cluster_events = [event]
            event_date = self._parse_date(event["date"])
            
            # Look for events within window
            for j in range(i + 1, len(timeline)):
                other_event = timeline[j]
                other_date = self._parse_date(other_event["date"])
                
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
                med_date = self._parse_date(event["date"])
                
                for j in range(i + 1, len(timeline)):
                    if j >= len(timeline):
                        break
                    
                    next_event = timeline[j]
                    if next_event["type"] == "symptom_reported":
                        symptom_date = self._parse_date(next_event["date"])
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
        
        # Run all correlation engines
        correlations = {
            "drug_symptom": self.drug_symptom_engine.analyze(
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