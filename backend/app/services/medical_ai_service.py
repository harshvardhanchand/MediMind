"""
Medical AI Analysis Service
Core orchestrator for medical notifications with embedding-based optimization
"""

import json
import time
import hashlib
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from .medical_embedding_service import medical_embedding_service
from .medical_vector_db import MedicalVectorDatabase, SimplifiedVectorSearch
from .gemini_service import analyze_medical_situation

logger = logging.getLogger(__name__)

class MedicalAIService:
    """
    Core medical AI service for proactive notifications
    Uses BioBERT embeddings + Gemini LLM for intelligent medical analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_db = MedicalVectorDatabase(db)
        self.vector_search = SimplifiedVectorSearch(db)
        
        # Cost tracking
        self.llm_cost_per_call = 0.02  # $0.02 per Gemini call
        self.embedding_cost_per_call = 0.001  # Minimal cost for BioBERT
        
        # Performance thresholds
        self.similarity_threshold = 0.85
        self.confidence_threshold = 0.8
    
    async def analyze_medical_event(
        self,
        user_id: str,
        trigger_type: str,  # "new_medication", "symptom_reported", "lab_result", etc.
        event_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for medical event analysis
        Returns list of notifications to create
        """
        start_time = time.time()
        
        try:
            logger.info(f"Analyzing medical event for user {user_id}: {trigger_type}")
            
            # 1. Build current medical profile
            medical_profile = await self._build_medical_profile(user_id, event_data)
            
            if not medical_profile:
                logger.warning(f"No medical profile available for user {user_id}")
                return []
            
            # 2. Create medical embedding
            medical_embedding = medical_embedding_service.create_medical_embedding(medical_profile)
            
            # 3. Search for similar situations
            similar_situations = await self.vector_search.find_similar_situations(
                medical_embedding, 
                medical_profile
            )
            
            # 4. Determine if we need LLM analysis
            llm_called = False
            analysis_result = None
            
            if similar_situations:
                # Found similar situation - adapt existing analysis
                logger.info(f"Found {len(similar_situations)} similar situations")
                analysis_result = await self._adapt_similar_analysis(
                    medical_profile, 
                    similar_situations[0]  # Use most similar
                )
                
                # Update usage count for the reused situation
                await self.vector_db.update_usage_count(similar_situations[0]["situation_id"])
                
            else:
                # No similar situation - call LLM
                logger.info("No similar situations found, calling LLM")
                analysis_result = await self._perform_llm_analysis(medical_profile)
                llm_called = True
                
                # Store new analysis in vector database
                if analysis_result and analysis_result.get("confidence", 0) >= self.confidence_threshold:
                    await self.vector_db.store_medical_situation(
                        medical_embedding,
                        medical_profile,
                        analysis_result,
                        analysis_result.get("confidence", 0.8)
                    )
            
            # 5. Create notifications from analysis
            notifications = await self._create_notifications_from_analysis(
                user_id, 
                analysis_result, 
                trigger_type,
                event_data
            )
            
            # 6. Log analysis for debugging
            processing_time = int((time.time() - start_time) * 1000)
            await self._log_analysis(
                user_id,
                trigger_type,
                medical_profile,
                medical_embedding,
                similar_situations,
                llm_called,
                analysis_result,
                processing_time,
                event_data
            )
            
            logger.info(f"Analysis complete: {len(notifications)} notifications generated")
            return notifications
            
        except Exception as e:
            logger.error(f"Medical event analysis failed: {str(e)}")
            return []
    
    async def _build_medical_profile(self, user_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build comprehensive medical profile from database
        """
        try:
            profile = {
                "user_id": user_id,
                "medications": [],
                "recent_symptoms": [],
                "health_conditions": [],
                "lab_results": [],
                "recent_event": event_data
            }
            
            # Get current medications
            medications_result = self.db.execute(
                """
                SELECT name, dosage, frequency, start_date, is_active
                FROM medications 
                WHERE user_id = %s AND is_active = true
                ORDER BY start_date DESC
                """,
                (user_id,)
            ).fetchall()
            
            profile["medications"] = [
                {
                    "name": row[0],
                    "dosage": row[1],
                    "frequency": row[2],
                    "start_date": row[3].isoformat() if row[3] else None
                }
                for row in medications_result
            ]
            
            # Get recent symptoms (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            symptoms_result = self.db.execute(
                """
                SELECT symptom, severity, reported_date, notes
                FROM symptoms 
                WHERE user_id = %s AND reported_date >= %s
                ORDER BY reported_date DESC
                LIMIT 10
                """,
                (user_id, cutoff_date)
            ).fetchall()
            
            profile["recent_symptoms"] = [
                {
                    "symptom": row[0],
                    "severity": row[1],
                    "date": row[2].isoformat() if row[2] else None,
                    "notes": row[3]
                }
                for row in symptoms_result
            ]
            
            # Get health conditions
            conditions_result = self.db.execute(
                """
                SELECT condition_name, diagnosed_date, severity, status
                FROM health_conditions 
                WHERE user_id = %s AND status = 'active'
                ORDER BY diagnosed_date DESC
                """,
                (user_id,)
            ).fetchall()
            
            profile["health_conditions"] = [
                {
                    "condition": row[0],
                    "diagnosed_date": row[1].isoformat() if row[1] else None,
                    "severity": row[2]
                }
                for row in conditions_result
            ]
            
            # Get recent lab results (last 90 days)
            lab_cutoff = datetime.now() - timedelta(days=90)
            labs_result = self.db.execute(
                """
                SELECT test_name, value, unit, reference_range, test_date
                FROM health_readings 
                WHERE user_id = %s AND test_date >= %s
                ORDER BY test_date DESC
                LIMIT 15
                """,
                (user_id, lab_cutoff)
            ).fetchall()
            
            profile["lab_results"] = [
                {
                    "test": row[0],
                    "value": row[1],
                    "unit": row[2],
                    "reference_range": row[3],
                    "date": row[4].isoformat() if row[4] else None
                }
                for row in labs_result
            ]
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to build medical profile: {str(e)}")
            return {}
    
    async def _adapt_similar_analysis(
        self, 
        current_profile: Dict[str, Any], 
        similar_situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt existing analysis to current situation (lightweight approach)
        """
        try:
            base_analysis = similar_situation["analysis_result"]
            
            # Simple adaptation - modify confidence and add current context
            adapted_analysis = base_analysis.copy()
            
            # Reduce confidence slightly since it's adapted
            original_confidence = adapted_analysis.get("confidence", 0.8)
            adapted_analysis["confidence"] = max(0.7, original_confidence - 0.1)
            
            # Add adaptation metadata
            adapted_analysis["adapted_from"] = similar_situation["situation_id"]
            adapted_analysis["similarity_score"] = similar_situation["similarity_score"]
            adapted_analysis["adaptation_timestamp"] = datetime.now().isoformat()
            
            # Customize messaging based on current event
            current_event = current_profile.get("recent_event", {})
            if current_event.get("type") == "new_medication":
                # Focus on drug interactions for new medications
                if "drug_interactions" in adapted_analysis:
                    adapted_analysis["priority_focus"] = "drug_interactions"
            
            return adapted_analysis
            
        except Exception as e:
            logger.error(f"Failed to adapt similar analysis: {str(e)}")
            # Fallback to LLM analysis
            return await self._perform_llm_analysis(current_profile)
    
    async def _perform_llm_analysis(self, medical_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform full LLM analysis using Gemini
        """
        try:
            # Create structured prompt for Gemini
            prompt = self._create_medical_analysis_prompt(medical_profile)
            
            # Call Gemini service
            llm_response = await analyze_medical_situation(prompt)
            
            if not llm_response:
                logger.error("No response from LLM analysis")
                return {}
            
            # Parse and structure the response
            analysis_result = self._parse_llm_response(llm_response)
            
            # Add metadata
            analysis_result["analysis_timestamp"] = datetime.now().isoformat()
            analysis_result["llm_model"] = "gemini-pro"
            analysis_result["confidence"] = analysis_result.get("confidence", 0.8)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return {}
    
    def _create_medical_analysis_prompt(self, medical_profile: Dict[str, Any]) -> str:
        """
        Create structured prompt for medical analysis
        """
        prompt_parts = [
            "MEDICAL ANALYSIS REQUEST",
            "Analyze the following medical situation for potential risks, drug interactions, and health recommendations.",
            "",
            "CURRENT MEDICATIONS:"
        ]
        
        medications = medical_profile.get("medications", [])
        if medications:
            for med in medications:
                prompt_parts.append(f"- {med.get('name', 'Unknown')} {med.get('dosage', '')} {med.get('frequency', '')}")
        else:
            prompt_parts.append("- None reported")
        
        prompt_parts.extend([
            "",
            "RECENT SYMPTOMS:"
        ])
        
        symptoms = medical_profile.get("recent_symptoms", [])
        if symptoms:
            for symptom in symptoms:
                prompt_parts.append(f"- {symptom.get('symptom', 'Unknown')} (Severity: {symptom.get('severity', 'Unknown')})")
        else:
            prompt_parts.append("- None reported")
        
        prompt_parts.extend([
            "",
            "HEALTH CONDITIONS:"
        ])
        
        conditions = medical_profile.get("health_conditions", [])
        if conditions:
            for condition in conditions:
                prompt_parts.append(f"- {condition.get('condition', 'Unknown')}")
        else:
            prompt_parts.append("- None reported")
        
        prompt_parts.extend([
            "",
            "RECENT LAB RESULTS:"
        ])
        
        labs = medical_profile.get("lab_results", [])
        if labs:
            for lab in labs[-5:]:  # Only show recent 5
                prompt_parts.append(f"- {lab.get('test', 'Unknown')}: {lab.get('value', 'N/A')} {lab.get('unit', '')}")
        else:
            prompt_parts.append("- None available")
            
        prompt_parts.extend([
            "",
            "Please analyze for:",
            "1. Drug interactions and contraindications",
            "2. Side effects to monitor",
            "3. Health trend concerns",
            "4. Recommended actions or monitoring",
            "",
            "Return analysis in JSON format with fields: drug_interactions, side_effects, health_trends, recommendations, confidence (0.0-1.0), severity (low/medium/high)."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format
        """
        try:
            # Try to parse as JSON first
            if llm_response.strip().startswith('{'):
                return json.loads(llm_response)
            
            # Fallback: extract key information from text response
            return {
                "raw_response": llm_response,
                "drug_interactions": self._extract_section(llm_response, "drug interaction"),
                "side_effects": self._extract_section(llm_response, "side effect"),
                "health_trends": self._extract_section(llm_response, "health trend"),
                "recommendations": self._extract_section(llm_response, "recommend"),
                "confidence": 0.8,
                "severity": "medium"
            }
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "raw_response": llm_response,
                "confidence": 0.7,
                "severity": "medium"
            }
    
    def _extract_section(self, text: str, keyword: str) -> List[str]:
        """
        Extract relevant sections from text response
        """
        lines = text.lower().split('\n')
        relevant_lines = [line.strip() for line in lines if keyword in line]
        return relevant_lines[:3]  # Return up to 3 relevant items
    
    async def _create_notifications_from_analysis(
        self,
        user_id: str,
        analysis_result: Dict[str, Any],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create notification objects from analysis results
        """
        notifications = []
        
        if not analysis_result:
            return notifications
        
        # Extract entity IDs from event data
        medication_id = event_data.get("medication_id") if event_data else None
        document_id = event_data.get("document_id") if event_data else None
        health_reading_id = event_data.get("health_reading_id") if event_data else None
        extracted_data_id = event_data.get("extracted_data_id") if event_data else None
        
        try:
            # Drug interaction notifications
            drug_interactions = analysis_result.get("drug_interactions", [])
            if drug_interactions:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "drug_interaction",
                    "severity": analysis_result.get("severity", "medium"),
                    "title": "Potential Drug Interaction Detected",
                    "message": self._format_drug_interaction_message(drug_interactions),
                    "metadata": {
                        "interactions": drug_interactions,
                        "trigger_type": trigger_type,
                        "confidence": analysis_result.get("confidence", 0.8)
                    },
                    # Entity relationships
                    "related_medication_id": medication_id,
                    "related_document_id": document_id,
                    "related_health_reading_id": health_reading_id,
                    "related_extracted_data_id": extracted_data_id
                }
                notifications.append(notification)
            
            # Side effect notifications
            side_effects = analysis_result.get("side_effects", [])
            if side_effects:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "side_effect_warning",
                    "severity": "medium",
                    "title": "Side Effects to Monitor",
                    "message": self._format_side_effects_message(side_effects),
                    "metadata": {
                        "side_effects": side_effects,
                        "trigger_type": trigger_type,
                        "confidence": analysis_result.get("confidence", 0.8)
                    },
                    # Entity relationships
                    "related_medication_id": medication_id,
                    "related_document_id": document_id,
                    "related_health_reading_id": health_reading_id,
                    "related_extracted_data_id": extracted_data_id
                }
                notifications.append(notification)
            
            # Health trend notifications
            health_trends = analysis_result.get("health_trends", [])
            if health_trends:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "health_trend",
                    "severity": "low",
                    "title": "Health Pattern Analysis",
                    "message": self._format_health_trends_message(health_trends),
                    "metadata": {
                        "trends": health_trends,
                        "trigger_type": trigger_type,
                        "confidence": analysis_result.get("confidence", 0.8)
                    },
                    # Entity relationships  
                    "related_medication_id": medication_id,
                    "related_document_id": document_id,
                    "related_health_reading_id": health_reading_id,
                    "related_extracted_data_id": extracted_data_id
                }
                notifications.append(notification)
            
            # Recommendation notifications
            recommendations = analysis_result.get("recommendations", [])
            if recommendations:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "medical_recommendation",
                    "severity": "low",
                    "title": "Health Recommendations",
                    "message": self._format_recommendations_message(recommendations),
                    "metadata": {
                        "recommendations": recommendations,
                        "trigger_type": trigger_type,
                        "confidence": analysis_result.get("confidence", 0.8)
                    },
                    # Entity relationships
                    "related_medication_id": medication_id,
                    "related_document_id": document_id,
                    "related_health_reading_id": health_reading_id,
                    "related_extracted_data_id": extracted_data_id
                }
                notifications.append(notification)
                
        except Exception as e:
            logger.error(f"Failed to create notifications: {str(e)}")
        
        return notifications
    
    def _format_drug_interaction_message(self, interactions: List[str]) -> str:
        """Format drug interaction message"""
        if isinstance(interactions, list) and interactions:
            return f"We've detected potential interactions between your medications: {', '.join(interactions[:2])}. Please consult your healthcare provider."
        return "Potential drug interactions detected with your current medications. Please review with your healthcare provider."
    
    def _format_side_effects_message(self, side_effects: List[str]) -> str:
        """Format side effects message"""
        if isinstance(side_effects, list) and side_effects:
            return f"Monitor for these potential side effects: {', '.join(side_effects[:3])}. Contact your doctor if you experience any of these symptoms."
        return "Please monitor for potential side effects from your current medications."
    
    def _format_health_trends_message(self, trends: List[str]) -> str:
        """Format health trends message"""
        if isinstance(trends, list) and trends:
            return f"Health pattern analysis shows: {trends[0]}. Consider discussing this trend with your healthcare provider."
        return "We've identified some health patterns worth discussing with your healthcare provider."
    
    def _format_recommendations_message(self, recommendations: List[str]) -> str:
        """Format recommendations message"""
        if isinstance(recommendations, list) and recommendations:
            return f"Health recommendation: {recommendations[0]}"
        return "We have some health recommendations based on your current medical profile."
    
    async def _log_analysis(
        self,
        user_id: str,
        trigger_type: str,
        medical_profile: Dict[str, Any],
        embedding: Any,
        similar_situations: List[Dict],
        llm_called: bool,
        analysis_result: Dict[str, Any],
        processing_time_ms: int,
        event_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log analysis for debugging and cost tracking
        """
        try:
            log_id = str(uuid.uuid4())
            profile_hash = medical_embedding_service.create_medical_hash(medical_profile)
            
            # Calculate cost
            llm_cost = self.llm_cost_per_call if llm_called else 0.0
            embedding_cost = self.embedding_cost_per_call
            total_cost = llm_cost + embedding_cost
            
            # Extract entity IDs from event data
            medication_id = event_data.get("medication_id") if event_data else None
            document_id = event_data.get("document_id") if event_data else None
            health_reading_id = event_data.get("health_reading_id") if event_data else None
            extracted_data_id = event_data.get("extracted_data_id") if event_data else None
            
            # Convert embedding to string for pgvector
            embedding_str = str(embedding.tolist()) if hasattr(embedding, 'tolist') else str([])
            
            self.db.execute(
                text("""
                    INSERT INTO ai_analysis_logs 
                    (id, user_id, trigger_type, medical_profile_hash, embedding, 
                     similarity_matches, llm_called, llm_cost, processing_time_ms, analysis_result,
                     related_medication_id, related_document_id, related_health_reading_id, related_extracted_data_id,
                     created_at)
                    VALUES (:id, :user_id, :trigger_type, :medical_profile_hash, :embedding::vector, 
                            :similarity_matches, :llm_called, :llm_cost, :processing_time_ms, :analysis_result,
                            :related_medication_id, :related_document_id, :related_health_reading_id, :related_extracted_data_id,
                            NOW())
                """),
                {
                    "id": log_id,
                    "user_id": user_id,
                    "trigger_type": trigger_type,
                    "medical_profile_hash": profile_hash,
                    "embedding": embedding_str,
                    "similarity_matches": json.dumps(similar_situations[:2]),  # Store top 2 matches
                    "llm_called": llm_called,
                    "llm_cost": total_cost,
                    "processing_time_ms": processing_time_ms,
                    "analysis_result": json.dumps(analysis_result),
                    "related_medication_id": medication_id,
                    "related_document_id": document_id,
                    "related_health_reading_id": health_reading_id,
                    "related_extracted_data_id": extracted_data_id
                }
            )
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log analysis: {str(e)}")

# Global service instance
def get_medical_ai_service(db: Session) -> MedicalAIService:
    """Get medical AI service instance"""
    return MedicalAIService(db) 