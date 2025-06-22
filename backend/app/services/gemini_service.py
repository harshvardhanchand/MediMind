"""
Gemini AI Service for Medical Analysis
Handles LLM calls for medical reasoning and analysis
"""

import os
import json
import logging
import asyncio
import re
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

class GeminiConfigurationError(Exception):
    """Raised when Gemini service is misconfigured"""
    pass

class GeminiAPIError(Exception):
    """Raised when Gemini API encounters an error"""
    pass

class GeminiMedicalService:
    """
    Service for medical analysis using Google's Gemini Pro model
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # FIXED: Fail fast on missing configuration
        if not self.api_key:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY environment variable is required but not found"
            )
        
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model with medical-focused configuration
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
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
            
            logger.info("GeminiMedicalService initialized successfully")
            
        except Exception as e:
            raise GeminiConfigurationError(f"Failed to initialize Gemini service: {str(e)}")
    
    async def analyze_medical_situation(self, medical_prompt: str) -> Optional[str]:
        """
        Analyze medical situation using Gemini Pro
        """
        try:
            # Combine medical context with user prompt
            full_prompt = f"{self.medical_context}\n\n{medical_prompt}"
            
            # FIXED: Validate prompt length (approximate token limit check)
            if len(full_prompt) > 30000:  # Conservative estimate for token limits
                logger.warning(f"Prompt length ({len(full_prompt)}) may exceed model limits")
                # Truncate medical context if needed
                max_context_len = 30000 - len(medical_prompt) - 100
                if max_context_len > 0:
                    truncated_context = self.medical_context[:max_context_len]
                    full_prompt = f"{truncated_context}\n\n{medical_prompt}"
                else:
                    raise GeminiAPIError("Medical prompt too long for model")
            
            logger.info("Sending request to Gemini Pro for medical analysis")
            
            # FIXED: Make the API call truly async using thread executor
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content, 
                full_prompt
            )
            
            if not response or not response.text:
                logger.error("Empty response from Gemini")
                return None
            
            logger.info("Successfully received response from Gemini")
            return response.text.strip()
            
        # FIXED: Granular error handling
        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Gemini API rate limit exceeded: {str(e)}")
            raise GeminiAPIError(f"Rate limit exceeded: {str(e)}")
        
        except google_exceptions.ServiceUnavailable as e:
            logger.error(f"Gemini service unavailable: {str(e)}")
            raise GeminiAPIError(f"Service unavailable: {str(e)}")
        
        except google_exceptions.InvalidArgument as e:
            logger.error(f"Invalid request to Gemini: {str(e)}")
            raise GeminiAPIError(f"Invalid request: {str(e)}")
        
        except google_exceptions.PermissionDenied as e:
            logger.error(f"Gemini API permission denied: {str(e)}")
            raise GeminiAPIError(f"Permission denied: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected Gemini analysis error: {str(e)}")
            raise GeminiAPIError(f"Analysis failed: {str(e)}")

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
            
        except GeminiAPIError:
            # Re-raise API errors
            raise
        except Exception as e:
            logger.error(f"Drug interaction analysis failed: {str(e)}")
            raise GeminiAPIError(f"Drug interaction analysis failed: {str(e)}")

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
            
        except GeminiAPIError:
            # Re-raise API errors
            raise
        except Exception as e:
            logger.error(f"Symptom-medication analysis failed: {str(e)}")
            raise GeminiAPIError(f"Symptom-medication analysis failed: {str(e)}")

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
            
        except GeminiAPIError:
            # Re-raise API errors
            raise
        except Exception as e:
            logger.error(f"Lab trend analysis failed: {str(e)}")
            raise GeminiAPIError(f"Lab trend analysis failed: {str(e)}")
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        FIXED: Robust JSON parsing with multiple extraction strategies
        """
        if not response:
            return {}
        
        # Strategy 1: Try to find JSON code block (```json ... ```)
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        json_match = re.search(json_block_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from code block")
        
        # Strategy 2: Find the largest valid JSON object
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(response):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete JSON object
                    try:
                        json_str = response[start_idx:i+1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue  # Try next potential JSON object
        
        # Strategy 3: Try parsing the entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Extract key-value pairs using regex
        logger.warning("Could not parse JSON, attempting key-value extraction")
        try:
            # Simple key-value extraction for common patterns
            result = {}
            
            # Extract arrays like "field": ["item1", "item2"]
            array_pattern = r'"([^"]+)":\s*\[(.*?)\]'
            for match in re.finditer(array_pattern, response, re.DOTALL):
                key = match.group(1)
                array_content = match.group(2)
                # Simple array parsing - split by comma and clean quotes
                items = [item.strip(' "\'') for item in array_content.split(',') if item.strip()]
                result[key] = items
            
            # Extract simple values like "field": "value" or "field": 0.8
            value_pattern = r'"([^"]+)":\s*(?:"([^"]*)"|(\d+\.?\d*)|true|false)'
            for match in re.finditer(value_pattern, response):
                key = match.group(1)
                if key not in result:  # Don't override arrays
                    value = match.group(2) or match.group(3)
                    if match.group(3):  # Numeric value
                        try:
                            result[key] = float(value) if '.' in value else int(value)
                        except ValueError:
                            result[key] = value
                    else:
                        result[key] = value
            
            if result:
                result["parse_method"] = "regex_extraction"
                result["confidence"] = 0.7
                return result
                
        except Exception as e:
            logger.warning(f"Regex extraction failed: {str(e)}")
        
        # Final fallback
        logger.warning("All JSON parsing strategies failed, returning raw response")
        return {
            "raw_response": response,
            "parse_error": True,
            "confidence": 0.3,
            "parse_method": "fallback"
        }

# FIXED: Lazy initialization to avoid creating invalid global instance
_gemini_service_instance = None

def get_gemini_service() -> GeminiMedicalService:
    """Get or create the global Gemini service instance"""
    global _gemini_service_instance
    if _gemini_service_instance is None:
        _gemini_service_instance = GeminiMedicalService()
    return _gemini_service_instance

# Convenience functions for backward compatibility
async def analyze_medical_situation(prompt: str) -> Optional[str]:
    """Analyze medical situation using Gemini"""
    service = get_gemini_service()
    return await service.analyze_medical_situation(prompt)

async def analyze_drug_interactions(medications: List[Dict[str, Any]]) -> Optional[str]:
    """Analyze drug interactions"""
    service = get_gemini_service()
    return await service.analyze_drug_interactions(medications)

async def analyze_symptoms_with_medications(
    symptoms: List[Dict[str, Any]], 
    medications: List[Dict[str, Any]]
) -> Optional[str]:
    """Analyze symptoms with medication context"""
    service = get_gemini_service()
    return await service.analyze_symptoms_with_medications(symptoms, medications) 