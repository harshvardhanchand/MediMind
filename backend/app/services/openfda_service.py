"""
OpenFDA API Service
Handles drug interaction checking using FDA's free API with significance filtering
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class OpenFDAService:
    """
    Service for interacting with OpenFDA API for drug interaction analysis
    """
    
    def __init__(self):
        self.base_url = "https://api.fda.gov"
        self.rate_limit_per_minute = 240  # FDA allows 240 requests per minute
        self.rate_limit_per_hour = 1000   # 1000 requests per hour
        
        # Significance thresholds
        self.min_notification_threshold = 0.6
        self.min_push_threshold = 0.8
        self.min_immediate_threshold = 0.9
        
        # Drug name mapping for common international variants
        self.drug_name_mapping = {
            "paracetamol": "acetaminophen",
            "crocin": "acetaminophen", 
            "disprin": "aspirin",
            "combiflam": ["ibuprofen", "acetaminophen"],  # Combination drug
            "shelcal": "calcium carbonate"
        }
    
    async def analyze_drug_interactions(
        self, 
        medications: List[Dict[str, Any]], 
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for drug interaction analysis with significance filtering
        """
        try:
            if not medications or len(medications) < 2:
                return self._create_empty_result()
            
            # Normalize drug names
            normalized_drugs = self._normalize_drug_names(medications)
            
            # Check FDA interactions
            fda_interactions = await self._check_fda_interactions(normalized_drugs)
            
            # Apply significance filtering
            significant_interactions = self._filter_significant_interactions(
                fda_interactions, 
                patient_context or {}
            )
            
            # Format final result
            return self._format_interaction_result(significant_interactions, patient_context)
            
        except Exception as e:
            logger.error(f"Drug interaction analysis failed: {str(e)}")
            return self._create_error_result(str(e))
    
    def _normalize_drug_names(self, medications: List[Dict[str, Any]]) -> List[str]:
        """
        Normalize drug names to handle international variants
        """
        normalized = []
        
        for med in medications:
            drug_name = med.get('name', '').lower().strip()
            
            # Check if it's in our mapping
            if drug_name in self.drug_name_mapping:
                mapped = self.drug_name_mapping[drug_name]
                if isinstance(mapped, list):
                    normalized.extend(mapped)  # Combination drug
                else:
                    normalized.append(mapped)
            else:
                normalized.append(drug_name)
        
        return list(set(normalized))  # Remove duplicates
    
    async def _check_fda_interactions(self, drug_names: List[str]) -> List[Dict[str, Any]]:
        """
        Query OpenFDA API for drug interactions
        """
        interactions = []
        
        async with aiohttp.ClientSession() as session:
            for i, drug1 in enumerate(drug_names):
                for drug2 in drug_names[i+1:]:
                    interaction = await self._query_drug_pair(session, drug1, drug2)
                    if interaction:
                        interactions.append(interaction)
        
        return interactions
    
    async def _query_drug_pair(
        self, 
        session: aiohttp.ClientSession, 
        drug1: str, 
        drug2: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query OpenFDA for a specific drug pair interaction
        """
        try:
            # Try adverse events API first
            url = f"{self.base_url}/drug/event.json"
            params = {
                "search": f'patient.drug.medicinalproduct:"{drug1}" AND patient.drug.medicinalproduct:"{drug2}"',
                "limit": 10
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_fda_interaction(drug1, drug2, data)
                elif response.status == 404:
                    # No interactions found - this is normal
                    return None
                else:
                    logger.warning(f"FDA API returned status {response.status} for {drug1} + {drug2}")
                    return None
            
        except Exception as e:
            logger.error(f"Failed to query FDA for {drug1} + {drug2}: {str(e)}")
            return None
    
    def _parse_fda_interaction(self, drug1: str, drug2: str, fda_data: Dict) -> Dict[str, Any]:
        """
        Parse FDA response to extract interaction information
        """
        if not fda_data.get('results'):
            return None
        
        # Analyze adverse events for severity indicators
        serious_events = 0
        total_events = len(fda_data['results'])
        common_reactions = {}
        
        for event in fda_data['results'][:10]:  # Analyze first 10 events
            # Check if event was serious
            if event.get('serious') == '1':
                serious_events += 1
            
            # Count reaction types
            reactions = event.get('patient', {}).get('reaction', [])
            for reaction in reactions:
                reaction_term = reaction.get('reactionmeddrapt', '').lower()
                if reaction_term:
                    common_reactions[reaction_term] = common_reactions.get(reaction_term, 0) + 1
        
        # Calculate base severity from FDA data
        serious_ratio = serious_events / total_events if total_events > 0 else 0
        
        return {
            "drug_pair": [drug1, drug2],
            "total_events": total_events,
            "serious_events": serious_events,
            "serious_ratio": serious_ratio,
            "common_reactions": dict(sorted(common_reactions.items(), key=lambda x: x[1], reverse=True)[:5]),
            "source": "FDA_ADVERSE_EVENTS"
        }
    
    def _filter_significant_interactions(
        self, 
        interactions: List[Dict[str, Any]], 
        patient_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply significance scoring and filtering
        """
        significant = []
        
        for interaction in interactions:
            score = self._calculate_significance_score(interaction, patient_context)
            
            if score >= self.min_notification_threshold:
                interaction['significance_score'] = score
                interaction['priority'] = self._score_to_priority(score)
                significant.append(interaction)
        
        # Sort by significance score (highest first)
        return sorted(significant, key=lambda x: x['significance_score'], reverse=True)
    
    def _calculate_significance_score(
        self, 
        interaction: Dict[str, Any], 
        patient_context: Dict[str, Any]
    ) -> float:
        """
        Calculate significance score for an interaction
        """
        base_score = 0.0
        
        # 1. FDA Event Severity (40% of score)
        serious_ratio = interaction.get('serious_ratio', 0)
        total_events = interaction.get('total_events', 0)
        
        if total_events >= 100:  # High confidence
            base_score += serious_ratio * 0.4
        elif total_events >= 10:  # Medium confidence
            base_score += serious_ratio * 0.3
        else:  # Low confidence
            base_score += serious_ratio * 0.2
        
        # 2. Reaction Severity Keywords (30% of score)
        reaction_score = self._score_reactions(interaction.get('common_reactions', {}))
        base_score += reaction_score * 0.3
        
        # 3. Patient Risk Factors (30% of score)
        patient_score = self._score_patient_risk(patient_context)
        base_score += patient_score * 0.3
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _score_reactions(self, reactions: Dict[str, int]) -> float:
        """
        Score reactions based on severity keywords
        """
        high_severity_keywords = [
            'death', 'cardiac arrest', 'respiratory failure', 'coma', 
            'seizure', 'stroke', 'bleeding', 'anaphylaxis', 'liver failure'
        ]
        
        moderate_severity_keywords = [
            'hypotension', 'tachycardia', 'confusion', 'syncope',
            'chest pain', 'dyspnea', 'rash', 'nausea', 'vomiting'
        ]
        
        max_score = 0.0
        total_weight = sum(reactions.values())
        
        for reaction, count in reactions.items():
            reaction_lower = reaction.lower()
            weight = count / total_weight if total_weight > 0 else 0
            
            if any(keyword in reaction_lower for keyword in high_severity_keywords):
                max_score = max(max_score, 0.9 * weight)
            elif any(keyword in reaction_lower for keyword in moderate_severity_keywords):
                max_score = max(max_score, 0.6 * weight)
            else:
                max_score = max(max_score, 0.3 * weight)
        
        return max_score
    
    def _score_patient_risk(self, patient_context: Dict[str, Any]) -> float:
        """
        Score patient-specific risk factors
        """
        risk_score = 0.0
        
        # Age factor
        age = patient_context.get('age', 0)
        if age >= 65:
            risk_score += 0.4
        elif age <= 18:
            risk_score += 0.3
        else:
            risk_score += 0.1
        
        # Health conditions
        conditions = patient_context.get('health_conditions', [])
        high_risk_conditions = ['kidney disease', 'liver disease', 'heart disease', 'diabetes']
        
        for condition in conditions:
            condition_name = condition.get('condition', '').lower()
            if any(risk_condition in condition_name for risk_condition in high_risk_conditions):
                risk_score += 0.2
        
        # Multiple medications (polypharmacy risk)
        medication_count = len(patient_context.get('medications', []))
        if medication_count >= 5:
            risk_score += 0.2
        elif medication_count >= 3:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _score_to_priority(self, score: float) -> str:
        """
        Convert significance score to priority level
        """
        if score >= self.min_immediate_threshold:
            return "IMMEDIATE"
        elif score >= self.min_push_threshold:
            return "HIGH"
        elif score >= self.min_notification_threshold:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _format_interaction_result(
        self, 
        interactions: List[Dict[str, Any]], 
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format the final interaction analysis result
        """
        if not interactions:
            return self._create_empty_result()
        
        # Categorize by priority
        immediate = [i for i in interactions if i['priority'] == 'IMMEDIATE']
        high = [i for i in interactions if i['priority'] == 'HIGH']
        medium = [i for i in interactions if i['priority'] == 'MEDIUM']
        
        return {
            "has_interactions": True,
            "total_interactions": len(interactions),
            "immediate_attention": immediate,
            "high_priority": high,
            "medium_priority": medium,
            "recommendations": self._generate_recommendations(interactions),
            "confidence": self._calculate_overall_confidence(interactions),
            "analysis_timestamp": datetime.now().isoformat(),
            "source": "OpenFDA"
        }
    
    def _generate_recommendations(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """
        Generate actionable recommendations based on interactions
        """
        recommendations = []
        
        immediate = [i for i in interactions if i['priority'] == 'IMMEDIATE']
        high = [i for i in interactions if i['priority'] == 'HIGH']
        
        if immediate:
            recommendations.append("⚠️ IMMEDIATE: Contact your doctor before taking these medications together")
            
        if high:
            recommendations.append("🔴 HIGH: Discuss these medication combinations with your healthcare provider")
            
        if len(interactions) >= 3:
            recommendations.append("📋 Consider medication review with pharmacist due to multiple interactions")
            
        recommendations.append("💊 Always inform healthcare providers about all medications you're taking")
        
        return recommendations
    
    def _calculate_overall_confidence(self, interactions: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence in the analysis
        """
        if not interactions:
            return 0.0
        
        total_events = sum(i.get('total_events', 0) for i in interactions)
        avg_events = total_events / len(interactions)
        
        # Higher confidence with more FDA events
        if avg_events >= 100:
            return 0.9
        elif avg_events >= 50:
            return 0.8
        elif avg_events >= 10:
            return 0.7
        else:
            return 0.6
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        Create result when no interactions found
        """
        return {
            "has_interactions": False,
            "total_interactions": 0,
            "immediate_attention": [],
            "high_priority": [],
            "medium_priority": [],
            "recommendations": ["✅ No significant drug interactions detected"],
            "confidence": 0.8,
            "analysis_timestamp": datetime.now().isoformat(),
            "source": "OpenFDA"
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        Create result when analysis fails
        """
        return {
            "has_interactions": False,
            "total_interactions": 0,
            "immediate_attention": [],
            "high_priority": [],
            "medium_priority": [],
            "recommendations": ["❌ Unable to check interactions. Please consult your healthcare provider."],
            "confidence": 0.0,
            "error": error_message,
            "analysis_timestamp": datetime.now().isoformat(),
            "source": "OpenFDA"
        }


# Global service instance
openfda_service = OpenFDAService() 