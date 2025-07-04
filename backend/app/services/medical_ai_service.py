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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import text, select

from .medical_embedding_service import medical_embedding_service
from .medical_vector_db import MedicalVectorDatabase, SimplifiedVectorSearch
from .gemini_service import analyze_medical_situation
from .openfda_service import openfda_service
from .correlation_engines import multi_correlation_analyzer

# Import models for ORM queries
from app.models.medication import Medication, MedicationStatus
from app.models.health_reading import HealthReading
from app.models.symptom import Symptom
from app.models.health_condition import HealthCondition

logger = logging.getLogger(__name__)

class MedicalAIService:
    """
    Core medical AI service for proactive notifications
    Uses BioBERT embeddings + Gemini LLM + OpenFDA API + Multi-Correlation Analysis for intelligent medical analysis
    """
    
    def __init__(self, db: AsyncSession, similarity_threshold: float = 0.85, confidence_threshold: float = 0.8):
        self.db = db
        self.vector_db = MedicalVectorDatabase(db)
        self.vector_search = SimplifiedVectorSearch(db)
        
        # Cost tracking
        self.llm_cost_per_call = 0.02  # $0.02 per Gemini call
        self.embedding_cost_per_call = 0.001  # Minimal cost for BioBERT
        
        # Performance thresholds (now configurable)
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold
        
        # Initialize embedding service with configurable threshold
        self.embedding_service = medical_embedding_service
        self.embedding_service.similarity_threshold = similarity_threshold
    
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
            
            # 2. Check for drug interactions using OpenFDA (if medications involved)
            fda_analysis = None
            if medical_profile.get("medications") and len(medical_profile["medications"]) >= 2:
                fda_analysis = await self._analyze_drug_interactions_fda(medical_profile)
            
            # 3. Comprehensive Multi-Correlation Analysis
            correlation_analysis = await multi_correlation_analyzer.analyze_comprehensive_correlations(
                medical_profile, 
                {"type": trigger_type, **event_data}
            )
            
            # 4. Create medical embedding for similarity search (for cost optimization)
            medical_embedding = medical_embedding_service.create_medical_embedding(medical_profile)
            
            # 5. Search for similar situations
            similar_situations = await self.vector_search.find_similar_situations(
                medical_embedding, 
                medical_profile
            )
            
            # 6. Determine if we need LLM analysis (only if correlations are insufficient)
            llm_called = False
            llm_analysis = None
            
            # Use LLM only if correlation analysis confidence is low or no high-priority correlations found
            high_priority_correlations = [
                c for c in correlation_analysis.get("correlations", []) 
                if c.get("priority_score", 0) > 0.8
            ]
            
            if not high_priority_correlations and not similar_situations:
                # No high-confidence correlations and no similar situations - use LLM
                logger.info("Low-confidence correlations, calling LLM for additional analysis")
                llm_analysis = await self._perform_llm_analysis(medical_profile)
                llm_called = True
                
                # Store new analysis in vector database
                if llm_analysis and llm_analysis.get("confidence", 0) >= self.confidence_threshold:
                    await self.vector_db.store_medical_situation(
                        medical_embedding,
                        medical_profile,
                        llm_analysis,
                        llm_analysis.get("confidence", 0.8)
                    )
            elif similar_situations:
                # Found similar situation - adapt existing analysis
                logger.info(f"Found {len(similar_situations)} similar situations, adapting analysis")
                llm_analysis = await self._adapt_similar_analysis(
                    medical_profile, 
                    similar_situations[0]  # Use most similar
                )
                
                # Update usage count for the reused situation
                await self.vector_db.update_usage_count(similar_situations[0]["situation_id"])
            
            # 7. Merge FDA, Correlation, and LLM analysis results
            merged_analysis = self._merge_all_analysis_results(fda_analysis, correlation_analysis, llm_analysis)
            
            # 8. Create notifications from merged analysis
            notifications = await self._create_notifications_from_analysis(
                user_id, 
                merged_analysis, 
                trigger_type,
                event_data
            )
            
            # 9. Log analysis for debugging
            processing_time = int((time.time() - start_time) * 1000)
            await self._log_analysis(
                user_id,
                trigger_type,
                medical_profile,
                medical_embedding,
                similar_situations,
                llm_called,
                merged_analysis,
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
        Build comprehensive medical profile from database using ORM
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
            
            # Get current medications using ORM
            medications_result = await self.db.execute(
                select(Medication).filter(
                    Medication.user_id == user_id,
                    Medication.status == MedicationStatus.ACTIVE
                ).order_by(Medication.start_date.desc())
            )
            medications = medications_result.scalars().all()
            
            profile["medications"] = [
                {
                    "name": med.name,
                    "dosage": med.dosage,
                    "frequency": med.frequency.value if med.frequency else None,
                    "start_date": med.start_date.isoformat() if med.start_date else None
                }
                for med in medications
            ]
            
            # Get recent symptoms (last 30 days) using ORM
            cutoff_date = datetime.now() - timedelta(days=30)
            symptoms_result = await self.db.execute(
                select(Symptom).filter(
                    Symptom.user_id == user_id,
                    Symptom.reported_date >= cutoff_date
                ).order_by(Symptom.reported_date.desc()).limit(10)
            )
            symptoms = symptoms_result.scalars().all()
            
            profile["recent_symptoms"] = [
                {
                    "symptom": symptom.symptom,
                    "severity": symptom.severity.value if symptom.severity else None,
                    "date": symptom.reported_date.isoformat() if symptom.reported_date else None,
                    "notes": symptom.notes
                }
                for symptom in symptoms
            ]
            
            # Get health conditions using ORM
            conditions = self.db.query(HealthCondition).filter(
                HealthCondition.user_id == user_id,
                HealthCondition.status == "active"
            ).order_by(HealthCondition.diagnosed_date.desc()).all()
            
            profile["health_conditions"] = [
                {
                    "condition": condition.condition_name,
                    "diagnosed_date": condition.diagnosed_date.isoformat() if condition.diagnosed_date else None,
                    "severity": condition.severity.value if condition.severity else None
                }
                for condition in conditions
            ]
            
            # Get recent lab results (last 90 days) using ORM
            lab_cutoff = datetime.now() - timedelta(days=90)
            health_readings = self.db.query(HealthReading).filter(
                HealthReading.user_id == user_id,
                HealthReading.reading_date >= lab_cutoff
            ).order_by(HealthReading.reading_date.desc()).limit(15).all()
            
            profile["lab_results"] = [
                {
                    "test": reading.reading_type.value if reading.reading_type else "Unknown",
                    "value": float(reading.numeric_value) if reading.numeric_value else reading.text_value,
                    "unit": reading.unit,
                    "reference_range": "Normal",  # Reference ranges can be added to model
                    "date": reading.reading_date.isoformat() if reading.reading_date else None
                }
                for reading in health_readings
            ]
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to build medical profile: {str(e)}")
            return {}
    
    async def _analyze_drug_interactions_fda(self, medical_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze drug interactions using OpenFDA API with significance filtering
        """
        try:
            medications = medical_profile.get("medications", [])
            if len(medications) < 2:
                return None
            
            # Create patient context for risk scoring
            patient_context = {
                "age": self._extract_patient_age(medical_profile),
                "health_conditions": medical_profile.get("health_conditions", []),
                "medications": medications,
                "recent_symptoms": medical_profile.get("recent_symptoms", [])
            }
            
            # Call OpenFDA service
            fda_result = await openfda_service.analyze_drug_interactions(
                medications, 
                patient_context
            )
            
            logger.info(f"FDA analysis result: {fda_result.get('total_interactions', 0)} interactions found")
            return fda_result
            
        except Exception as e:
            logger.error(f"FDA drug interaction analysis failed: {str(e)}")
            return None
    
    def _extract_patient_age(self, medical_profile: Dict[str, Any]) -> int:
        """
        Extract patient age from medical profile (placeholder implementation)
        """
        # Age field can be added to user profile for more accurate analysis
        return 35  # Default age for now
    
    def _merge_all_analysis_results(
        self, 
        fda_analysis: Optional[Dict[str, Any]], 
        correlation_analysis: Dict[str, Any],
        llm_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge FDA, correlation, and LLM analysis results with correlation analysis taking priority
        """
        # Start with correlation analysis as the foundation
        merged = {
            "correlations": correlation_analysis.get("correlations", []),
            "insights": correlation_analysis.get("insights", {}),
            "correlation_confidence": self._calculate_correlation_confidence(correlation_analysis),
            "analysis_sources": ["correlation_engine"]
        }
        
        # Add FDA analysis for drug interactions
        if fda_analysis and fda_analysis.get("has_interactions"):
            merged["fda_drug_interactions"] = fda_analysis
            merged["analysis_sources"].append("openfda")
            
            # Convert FDA interactions to correlation format for consistency
            fda_correlations = self._convert_fda_to_correlation_format(fda_analysis)
            merged["correlations"].extend(fda_correlations)
        
        # Add LLM analysis if available (lowest priority)
        if llm_analysis:
            merged["llm_supplement"] = llm_analysis
            merged["analysis_sources"].append("gemini_llm")
            
            # Add LLM insights that aren't covered by correlations
            merged = self._merge_llm_insights(merged, llm_analysis)
        
        # Prioritize and deduplicate all correlations
        merged["correlations"] = self._prioritize_and_deduplicate_correlations(merged["correlations"])
        
        # Generate final recommendations from all sources
        merged["final_recommendations"] = self._generate_final_recommendations(merged)
        
        # Calculate overall confidence
        merged["overall_confidence"] = self._calculate_overall_confidence(merged)
        
        return merged
    
    def _calculate_correlation_confidence(self, correlation_analysis: Dict[str, Any]) -> float:
        """Calculate confidence from correlation analysis"""
        correlations = correlation_analysis.get("correlations", [])
        if not correlations:
            return 0.0
        
        # Use average of top 3 correlations
        top_correlations = sorted(correlations, key=lambda x: x.get("confidence", 0), reverse=True)[:3]
        avg_confidence = sum(c.get("confidence", 0) for c in top_correlations) / len(top_correlations)
        
        return avg_confidence
    
    def _convert_fda_to_correlation_format(self, fda_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert FDA analysis to correlation format"""
        correlations = []
        
        # Convert immediate attention interactions
        for interaction in fda_analysis.get("immediate_attention", []):
            correlations.append({
                "type": "drug_interaction_fda",
                "medication": " + ".join(interaction.get("drug_pair", [])),
                "confidence": 0.95,
                "severity": "high",
                "priority_score": 0.95,
                "recommendation": "⚠️ IMMEDIATE: Contact your doctor before taking these medications together",
                "source": "OpenFDA"
            })
        
        # Convert high priority interactions
        for interaction in fda_analysis.get("high_priority", []):
            correlations.append({
                "type": "drug_interaction_fda",
                "medication": " + ".join(interaction.get("drug_pair", [])),
                "confidence": 0.85,
                "severity": "medium", 
                "priority_score": 0.85,
                "recommendation": "🔴 HIGH: Discuss these medication combinations with your healthcare provider",
                "source": "OpenFDA"
            })
        
        return correlations
    
    def _merge_llm_insights(self, merged: Dict[str, Any], llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM insights that complement correlation analysis"""
        # Add LLM recommendations that aren't covered by correlations
        llm_recommendations = llm_analysis.get("recommendations", [])
        correlation_topics = set()
        
        # Extract topics covered by correlations
        for correlation in merged.get("correlations", []):
            if correlation.get("medication"):
                correlation_topics.add(correlation["medication"].lower())
            if correlation.get("symptom"):
                correlation_topics.add(correlation["symptom"].lower())
            if correlation.get("lab_test"):
                correlation_topics.add(correlation["lab_test"].lower())
        
        # Add LLM recommendations for uncovered topics
        supplemental_recommendations = []
        for rec in llm_recommendations:
            rec_lower = rec.lower()
            # Check if recommendation covers new ground
            if not any(topic in rec_lower for topic in correlation_topics):
                supplemental_recommendations.append(rec)
        
        if supplemental_recommendations:
            if "insights" not in merged:
                merged["insights"] = {}
            merged["insights"]["llm_supplemental"] = supplemental_recommendations
        
        return merged
    
    def _prioritize_and_deduplicate_correlations(self, correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize and remove duplicate correlations"""
        # Sort by priority score
        sorted_correlations = sorted(correlations, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Deduplicate based on similar entities
        deduplicated = []
        seen_combinations = set()
        
        for correlation in sorted_correlations:
            # Create a signature for this correlation
            signature_parts = []
            for key in ["medication", "symptom", "lab_test", "type"]:
                if correlation.get(key):
                    signature_parts.append(f"{key}:{correlation[key].lower()}")
            
            signature = "|".join(sorted(signature_parts))
            
            if signature not in seen_combinations:
                seen_combinations.add(signature)
                deduplicated.append(correlation)
        
        return deduplicated[:10]  # Return top 10 correlations
    
    def _generate_final_recommendations(self, merged_analysis: Dict[str, Any]) -> List[str]:
        """Generate final prioritized recommendations"""
        recommendations = []
        
        # Add correlation-based recommendations (highest priority)
        correlation_insights = merged_analysis.get("insights", {})
        if correlation_insights.get("recommendations"):
            recommendations.extend(correlation_insights["recommendations"][:3])
        
        # Add FDA recommendations
        fda_analysis = merged_analysis.get("fda_drug_interactions", {})
        if fda_analysis.get("recommendations"):
            recommendations.extend(fda_analysis["recommendations"][:2])
        
        # Add supplemental LLM recommendations
        llm_supplemental = correlation_insights.get("llm_supplemental", [])
        recommendations.extend(llm_supplemental[:2])
        
        # Deduplicate and limit
        unique_recommendations = []
        for rec in recommendations:
            if rec not in unique_recommendations:
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]  # Top 5 recommendations
    
    def _calculate_overall_confidence(self, merged_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence from all analysis sources"""
        confidences = []
        
        # Correlation analysis confidence (highest weight)
        corr_confidence = merged_analysis.get("correlation_confidence", 0)
        if corr_confidence > 0:
            confidences.append(corr_confidence * 0.6)  # 60% weight
        
        # FDA confidence
        fda_analysis = merged_analysis.get("fda_drug_interactions", {})
        if fda_analysis.get("confidence"):
            confidences.append(fda_analysis["confidence"] * 0.3)  # 30% weight
        
        # LLM confidence (lowest weight)
        llm_analysis = merged_analysis.get("llm_supplement", {})
        if llm_analysis.get("confidence"):
            confidences.append(llm_analysis["confidence"] * 0.1)  # 10% weight
        
        return sum(confidences) if confidences else 0.5
    
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
        Create notification objects from comprehensive analysis results
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
            # Create notifications from correlations (primary source)
            correlations = analysis_result.get("correlations", [])
            correlation_notifications = self._create_correlation_notifications(
                user_id, correlations, trigger_type, event_data
            )
            notifications.extend(correlation_notifications)
            
            # Create notifications from insights
            insights = analysis_result.get("insights", {})
            if insights.get("risk_alerts"):
                risk_notifications = self._create_risk_alert_notifications(
                    user_id, insights["risk_alerts"], trigger_type, event_data
                )
                notifications.extend(risk_notifications)
            
            # Create summary notification if we have significant findings
            if analysis_result.get("overall_confidence", 0) > 0.7:
                summary_notification = self._create_summary_notification(
                    user_id, analysis_result, trigger_type, event_data
                )
                if summary_notification:
                    notifications.append(summary_notification)
            
            # Create monitoring notifications
            monitoring_suggestions = insights.get("monitoring_suggestions", [])
            if monitoring_suggestions:
                monitoring_notification = self._create_monitoring_notification(
                    user_id, monitoring_suggestions, trigger_type, event_data
                )
                if monitoring_notification:
                    notifications.append(monitoring_notification)
                    
        except Exception as e:
            logger.error(f"Failed to create notifications: {str(e)}")
        
        return notifications[:5]  # Limit to top 5 notifications
    
    def _create_correlation_notifications(
        self,
        user_id: str,
        correlations: List[Dict[str, Any]],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create notifications from correlation analysis"""
        notifications = []
        
        # Group correlations by type for better notification organization
        correlation_groups = {}
        for correlation in correlations[:3]:  # Top 3 correlations
            corr_type = correlation.get("type", "unknown")
            if corr_type not in correlation_groups:
                correlation_groups[corr_type] = []
            correlation_groups[corr_type].append(correlation)
        
        # Create notifications for each correlation type
        for corr_type, corr_list in correlation_groups.items():
            notification = self._create_correlation_type_notification(
                user_id, corr_type, corr_list, trigger_type, event_data
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def _create_correlation_type_notification(
        self,
        user_id: str,
        correlation_type: str,
        correlations: List[Dict[str, Any]],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Create notification for a specific correlation type"""
        if not correlations:
            return None
        
        # Use the highest priority correlation for the notification
        primary_correlation = max(correlations, key=lambda x: x.get("priority_score", 0))
        
        # Determine notification type and severity
        notification_type, severity = self._map_correlation_to_notification_type(correlation_type, primary_correlation)
        
        # Generate title and message
        title, message = self._generate_correlation_notification_content(correlation_type, correlations)
        
        # Extract entity IDs
        medication_id = event_data.get("medication_id") if event_data else None
        document_id = event_data.get("document_id") if event_data else None
        health_reading_id = event_data.get("health_reading_id") if event_data else None
        extracted_data_id = event_data.get("extracted_data_id") if event_data else None
        
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": notification_type,
            "severity": severity,
            "title": title,
            "message": message,
            "metadata": {
                "correlations": correlations,
                "correlation_type": correlation_type,
                "trigger_type": trigger_type,
                "confidence": primary_correlation.get("confidence", 0.8),
                "priority_score": primary_correlation.get("priority_score", 0.5)
            },
            # Entity relationships
            "related_medication_id": medication_id,
            "related_document_id": document_id,
            "related_health_reading_id": health_reading_id,
            "related_extracted_data_id": extracted_data_id
        }
    
    def _map_correlation_to_notification_type(self, correlation_type: str, correlation: Dict[str, Any]) -> Tuple[str, str]:
        """Map correlation type to notification type and severity"""
        type_mapping = {
            "drug_symptom_correlation": ("side_effect_warning", correlation.get("severity", "medium")),
            "lab_symptom_correlation": ("health_trend", "medium"),
            "drug_lab_correlation": ("monitoring_alert", correlation.get("concern_level", "medium")),
            "drug_interaction_fda": ("drug_interaction", correlation.get("severity", "high")),
            "temporal_cluster": ("pattern_alert", "low"),
            "medication_symptom_sequence": ("side_effect_warning", "medium")
        }
        
        return type_mapping.get(correlation_type, ("medical_insight", "low"))
    
    def _generate_correlation_notification_content(self, correlation_type: str, correlations: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate title and message for correlation notification"""
        primary = correlations[0]
        
        if correlation_type == "drug_symptom_correlation":
            title = "Medication Side Effect Detected"
            symptom = primary.get("symptom", "symptom")
            medication = primary.get("medication", "medication")
            message = f"Your {symptom} may be related to {medication}. {primary.get('recommendation', 'Consult your healthcare provider.')}"
            
        elif correlation_type == "lab_symptom_correlation":
            title = "Lab Result Explains Symptom"
            symptom = primary.get("symptom", "symptom")
            lab_test = primary.get("lab_test", "lab test")
            lab_value = primary.get("lab_value", "abnormal")
            message = f"Your {symptom} may be explained by {lab_test} level ({lab_value}). {primary.get('recommendation', 'Discuss with your doctor.')}"
            
        elif correlation_type == "drug_lab_correlation":
            title = "Medication Monitoring Alert"
            medication = primary.get("medication", "medication")
            lab_test = primary.get("lab_test", "lab test")
            message = f"Monitor {lab_test} levels while taking {medication}. {primary.get('recommendation', 'Regular monitoring recommended.')}"
            
        elif correlation_type == "drug_interaction_fda":
            title = "Drug Interaction Warning"
            medication = primary.get("medication", "medications")
            message = f"Potential interaction detected: {medication}. {primary.get('recommendation', 'Contact your healthcare provider.')}"
            
        elif correlation_type == "temporal_cluster":
            title = "Medical Events Pattern"
            event_count = len(correlations)
            message = f"Multiple medical events ({event_count}) occurred close together. Consider reviewing for connections."
            
        else:
            title = "Medical Correlation Detected"
            message = primary.get("recommendation", "Review this correlation with your healthcare provider.")
        
        return title, message
    
    def _create_risk_alert_notifications(
        self,
        user_id: str,
        risk_alerts: List[str],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create notifications for risk alerts"""
        notifications = []
        
        for alert in risk_alerts[:2]:  # Top 2 risk alerts
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "risk_alert",
                "severity": "high",
                "title": "High Risk Medical Alert",
                "message": alert,
                "metadata": {
                    "alert_type": "risk_alert",
                    "trigger_type": trigger_type,
                    "requires_immediate_attention": True
                },
                # Entity relationships
                "related_medication_id": event_data.get("medication_id") if event_data else None,
                "related_document_id": event_data.get("document_id") if event_data else None,
                "related_health_reading_id": event_data.get("health_reading_id") if event_data else None,
                "related_extracted_data_id": event_data.get("extracted_data_id") if event_data else None
            }
            notifications.append(notification)
        
        return notifications
    
    def _create_summary_notification(
        self,
        user_id: str,
        analysis_result: Dict[str, Any],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Create summary notification for comprehensive analysis"""
        insights = analysis_result.get("insights", {})
        summary = insights.get("summary")
        
        if not summary:
            return None
        
        correlation_count = len(analysis_result.get("correlations", []))
        confidence = analysis_result.get("overall_confidence", 0.5)
        
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "comprehensive_analysis",
            "severity": "medium",
            "title": "Medical Analysis Summary",
            "message": f"{summary} Found {correlation_count} correlations with {confidence:.1%} confidence.",
            "metadata": {
                "analysis_type": "comprehensive",
                "trigger_type": trigger_type,
                "correlation_count": correlation_count,
                "confidence": confidence,
                "analysis_sources": analysis_result.get("analysis_sources", [])
            },
            # Entity relationships
            "related_medication_id": event_data.get("medication_id") if event_data else None,
            "related_document_id": event_data.get("document_id") if event_data else None,
            "related_health_reading_id": event_data.get("health_reading_id") if event_data else None,
            "related_extracted_data_id": event_data.get("extracted_data_id") if event_data else None
        }
    
    def _create_monitoring_notification(
        self,
        user_id: str,
        monitoring_suggestions: List[str],
        trigger_type: str,
        event_data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Create notification for monitoring suggestions"""
        if not monitoring_suggestions:
            return None
        
        # Combine multiple monitoring suggestions
        message = "Recommended monitoring: " + "; ".join(monitoring_suggestions[:3])
        
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "monitoring_recommendation",
            "severity": "low",
            "title": "Monitoring Recommendations",
            "message": message,
            "metadata": {
                "monitoring_suggestions": monitoring_suggestions,
                "trigger_type": trigger_type,
                "suggestion_count": len(monitoring_suggestions)
            },
            # Entity relationships
            "related_medication_id": event_data.get("medication_id") if event_data else None,
            "related_document_id": event_data.get("document_id") if event_data else None,
            "related_health_reading_id": event_data.get("health_reading_id") if event_data else None,
            "related_extracted_data_id": event_data.get("extracted_data_id") if event_data else None
        }
    
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
            
            await self.db.execute(
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
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log analysis: {str(e)}")

# Global service instance
def get_medical_ai_service(
    db: AsyncSession, 
    similarity_threshold: float = 0.85, 
    confidence_threshold: float = 0.8
) -> MedicalAIService:
    """Get medical AI service instance with configurable thresholds"""
    return MedicalAIService(db, similarity_threshold, confidence_threshold) 