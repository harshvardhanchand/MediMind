"""
Gemini AI Service for Medical Analysis
Handles LLM calls for medical reasoning and analysis
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class GeminiMedicalService:
    """
    Service for medical analysis using Google's Gemini Pro model
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model with medical-focused configuration
        self.model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent medical analysis
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
                "candidate_count": 1,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }
        )
        
        # Medical context prefix
        self.medical_context = """
        You are a medical analysis AI assistant designed to help identify potential health risks and provide recommendations. 
        Your analysis should be:
        1. Conservative and evidence-based
        2. Focused on patient safety
        3. Clear about when to consult healthcare providers
        4. Never provide definitive diagnoses
        5. Always encourage professional medical consultation for serious concerns
        
        Important: Your responses should be informational only and not replace professional medical advice.
        """
    
    async def analyze_medical_situation(self, medical_prompt: str) -> Optional[str]:
        """
        Analyze medical situation using Gemini Pro
        """
        if not self.api_key:
            logger.error("Gemini API key not configured")
            return None
        
        try:
            # Combine medical context with user prompt
            full_prompt = f"{self.medical_context}\n\n{medical_prompt}"
            
            logger.info("Sending request to Gemini Pro for medical analysis")
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            if not response or not response.text:
                logger.error("Empty response from Gemini")
                return None
            
            logger.info("Successfully received response from Gemini")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return None
    
    async def analyze_drug_interactions(self, medications: List[Dict[str, Any]]) -> Optional[str]:
        """
        Specialized drug interaction analysis
        """
        if not medications:
            return None
        
        try:
            # Create drug interaction specific prompt
            med_list = []
            for med in medications:
                med_info = f"{med.get('name', 'Unknown')}"
                if med.get('dosage'):
                    med_info += f" {med.get('dosage')}"
                if med.get('frequency'):
                    med_info += f" {med.get('frequency')}"
                med_list.append(med_info)
            
            prompt = f"""
            DRUG INTERACTION ANALYSIS
            
            Please analyze the following medications for potential interactions:
            {chr(10).join(f'- {med}' for med in med_list)}
            
            Focus on:
            1. Known dangerous interactions
            2. Moderate interactions that require monitoring
            3. Potential side effects to watch for
            4. Recommendations for timing or dosage adjustments
            
            Format your response as JSON with these fields:
            - "high_risk_interactions": [] (list of serious interaction warnings)
            - "moderate_interactions": [] (list of interactions requiring monitoring)
            - "side_effects_to_monitor": [] (list of symptoms to watch for)
            - "recommendations": [] (list of actionable recommendations)
            - "confidence": 0.0-1.0 (confidence in analysis)
            - "requires_immediate_attention": true/false
            """
            
            return await self.analyze_medical_situation(prompt)
            
        except Exception as e:
            logger.error(f"Drug interaction analysis failed: {str(e)}")
            return None
    
    async def analyze_symptoms_with_medications(
        self, 
        symptoms: List[Dict[str, Any]], 
        medications: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Analyze symptoms in context of current medications
        """
        try:
            symptom_list = []
            for symptom in symptoms:
                symptom_info = f"{symptom.get('symptom', 'Unknown')}"
                if symptom.get('severity'):
                    symptom_info += f" (Severity: {symptom.get('severity')})"
                if symptom.get('date'):
                    symptom_info += f" - {symptom.get('date')}"
                symptom_list.append(symptom_info)
            
            med_list = []
            for med in medications:
                med_info = f"{med.get('name', 'Unknown')} {med.get('dosage', '')}"
                med_list.append(med_info)
            
            prompt = f"""
            SYMPTOM AND MEDICATION ANALYSIS
            
            Current Medications:
            {chr(10).join(f'- {med}' for med in med_list)}
            
            Recent Symptoms:
            {chr(10).join(f'- {symptom}' for symptom in symptom_list)}
            
            Please analyze:
            1. Could any symptoms be side effects of current medications?
            2. Do symptoms suggest medication interactions?
            3. Are there concerning patterns that need immediate attention?
            4. What monitoring or actions are recommended?
            
            Format response as JSON with:
            - "medication_related_symptoms": [] (symptoms likely caused by medications)
            - "interaction_indicators": [] (symptoms suggesting drug interactions)
            - "concerning_patterns": [] (worrying symptom patterns)
            - "immediate_actions": [] (urgent recommendations)
            - "monitoring_suggestions": [] (ongoing monitoring advice)
            - "severity": "low/medium/high"
            - "confidence": 0.0-1.0
            """
            
            return await self.analyze_medical_situation(prompt)
            
        except Exception as e:
            logger.error(f"Symptom-medication analysis failed: {str(e)}")
            return None
    
    async def analyze_lab_trends(self, lab_results: List[Dict[str, Any]]) -> Optional[str]:
        """
        Analyze lab result trends for concerning patterns
        """
        if not lab_results:
            return None
        
        try:
            lab_list = []
            for lab in lab_results:
                lab_info = f"{lab.get('test', 'Unknown')}: {lab.get('value', 'N/A')} {lab.get('unit', '')}"
                if lab.get('reference_range'):
                    lab_info += f" (Ref: {lab.get('reference_range')})"
                if lab.get('date'):
                    lab_info += f" - {lab.get('date')}"
                lab_list.append(lab_info)
            
            prompt = f"""
            LAB RESULTS TREND ANALYSIS
            
            Recent Lab Results (chronological):
            {chr(10).join(f'- {lab}' for lab in lab_list)}
            
            Please analyze for:
            1. Values outside normal ranges
            2. Concerning trends over time
            3. Patterns that suggest specific conditions
            4. Recommendations for follow-up testing
            5. Lifestyle or medication considerations
            
            Format response as JSON:
            - "abnormal_values": [] (values outside normal range)
            - "concerning_trends": [] (worrying patterns over time)
            - "potential_conditions": [] (conditions suggested by patterns)
            - "follow_up_tests": [] (recommended additional testing)
            - "lifestyle_recommendations": [] (diet, exercise, etc.)
            - "urgency": "low/medium/high"
            - "confidence": 0.0-1.0
            """
            
            return await self.analyze_medical_situation(prompt)
            
        except Exception as e:
            logger.error(f"Lab trend analysis failed: {str(e)}")
            return None
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini, with fallback handling
        """
        if not response:
            return {}
        
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            # If no JSON found, try to parse the whole response
            return json.loads(response)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, returning structured fallback")
            return {
                "raw_response": response,
                "parse_error": True,
                "confidence": 0.6
            }

# Global service instance
gemini_service = GeminiMedicalService()

# Convenience functions for backward compatibility
async def analyze_medical_situation(prompt: str) -> Optional[str]:
    """Analyze medical situation using Gemini"""
    return await gemini_service.analyze_medical_situation(prompt)

async def analyze_drug_interactions(medications: List[Dict[str, Any]]) -> Optional[str]:
    """Analyze drug interactions"""
    return await gemini_service.analyze_drug_interactions(medications)

async def analyze_symptoms_with_medications(
    symptoms: List[Dict[str, Any]], 
    medications: List[Dict[str, Any]]
) -> Optional[str]:
    """Analyze symptoms with medication context"""
    return await gemini_service.analyze_symptoms_with_medications(symptoms, medications) 