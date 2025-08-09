"""
Selective reprocessing service for handling partial AI reprocessing of changed fields.
Enhanced with CRUD operations and temporal medical context management.
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.extracted_data_repo import ExtractedDataRepository
from app.models.extracted_data import ExtractedData
from app.models.medication import Medication, MedicationStatus
from app.models.health_reading import HealthReading
from app.models.symptom import Symptom
from app.services.gemini_service import get_gemini_service


logger = logging.getLogger(__name__)


class ClockProvider(ABC):
    """Abstract clock provider for testable time operations"""

    @abstractmethod
    def now(self) -> datetime:
        pass

    @abstractmethod
    def today(self) -> date:
        pass


class SystemClockProvider(ClockProvider):
    """Production clock provider using system time"""

    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return date.today()


class MockClockProvider(ClockProvider):
    """Test clock provider with fixed time"""

    def __init__(self, fixed_time: datetime):
        self.fixed_time = fixed_time

    def now(self) -> datetime:
        return self.fixed_time

    def today(self) -> date:
        return self.fixed_time.date()


class TemporalMedicalContext:
    """Manages temporal relevance of medical data"""

    def __init__(self, clock_provider: ClockProvider = None):
        self.clock = clock_provider or SystemClockProvider()

    def is_medication_active(self, medication_data: Dict[str, Any]) -> bool:
        """Check if a medication is currently active/relevant"""
        try:

            status = medication_data.get("status", "").lower()
            if status in ["discontinued", "completed", "expired"]:
                return False

            end_date_str = medication_data.get("end_date")
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(
                        end_date_str.replace("Z", "+00:00")
                    ).date()
                    if end_date < self.clock.today():
                        return False
                except:
                    pass

            duration = medication_data.get("duration") or medication_data.get(
                "frequency_details", ""
            )
            start_date_str = medication_data.get("start_date")

            if duration and start_date_str and "day" in duration.lower():
                try:
                    start_date = datetime.fromisoformat(
                        start_date_str.replace("Z", "+00:00")
                    ).date()

                    import re

                    days_match = re.search(r"(\d+)\s*days?", duration.lower())
                    if days_match:
                        duration_days = int(days_match.group(1))
                        expected_end = start_date + timedelta(days=duration_days)
                        if expected_end < self.clock.today():
                            return False
                except:
                    pass

            return True

        except Exception as e:
            logger.warning(f"Error checking medication activity: {e}")
            return True

    def get_medical_relevance_score(
        self, item_data: Dict[str, Any], item_type: str
    ) -> float:
        """Calculate relevance score (0.0 to 1.0) for medical data"""
        try:
            base_score = 1.0

            if item_type == "medication":

                if not self.is_medication_active(item_data):

                    base_score = 0.3

                    end_date_str = item_data.get("end_date") or item_data.get(
                        "start_date"
                    )
                    if end_date_str:
                        try:
                            end_date = datetime.fromisoformat(
                                end_date_str.replace("Z", "+00:00")
                            ).date()
                            days_expired = (self.clock.today() - end_date).days
                            if days_expired > 90:
                                base_score = 0.1
                        except:
                            pass

            elif item_type == "symptom":
                # Recent symptoms more relevant
                symptom_date_str = item_data.get("date_time") or item_data.get("date")
                if symptom_date_str:
                    try:
                        symptom_date = datetime.fromisoformat(
                            symptom_date_str.replace("Z", "+00:00")
                        ).date()
                        days_old = (self.clock.today() - symptom_date).days
                        if days_old > 30:
                            base_score = max(
                                0.2, 1.0 - (days_old / 365)
                            )  # Decay over a year
                    except:
                        pass

            elif item_type == "lab_result":
                # Lab results decay in relevance over time
                result_date_str = item_data.get("date_time") or item_data.get("date")
                if result_date_str:
                    try:
                        result_date = datetime.fromisoformat(
                            result_date_str.replace("Z", "+00:00")
                        ).date()
                        days_old = (self.clock.today() - result_date).days
                        if days_old > 90:
                            base_score = max(
                                0.3, 1.0 - (days_old / 730)
                            )  # Decay over 2 years
                    except:
                        pass

            return base_score

        except Exception as e:
            logger.warning(f"Error calculating relevance score: {e}")
            return 1.0


class CRUDOperationHandler:
    """Handles CRUD operations with intelligent reprocessing"""

    def __init__(self, db: AsyncSession, clock_provider: ClockProvider = None):
        self.db = db
        self.clock = clock_provider or SystemClockProvider()
        self.temporal_context = TemporalMedicalContext(self.clock)

    async def handle_crud_operation(
        self,
        operation_type: str,
        data_type: str,
        item_data: Dict[str, Any],
        user_id: str,
        affected_documents: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle CRUD operations with intelligent reprocessing

        Returns:
            Dict containing reprocessing results and affected contexts
        """
        try:
            logger.info(f"Handling {operation_type} operation for {data_type}")

            # Determine what contexts are affected
            affected_contexts = await self._determine_affected_contexts(
                operation_type, data_type, item_data, user_id
            )

            # Get current medical profile for context
            current_profile = await self._build_current_medical_profile(user_id)

            # Determine reprocessing strategy
            strategy = self._determine_reprocessing_strategy(
                operation_type, data_type, item_data, affected_contexts
            )

            # Execute reprocessing based on strategy
            results = await self._execute_reprocessing_strategy(
                strategy, current_profile, item_data, affected_contexts
            )

            return {
                "operation_type": operation_type,
                "data_type": data_type,
                "affected_contexts": affected_contexts,
                "strategy": strategy,
                "results": results,
                "timestamp": self.clock.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error handling CRUD operation: {e}", exc_info=True)
            return {"error": str(e)}

    async def _determine_affected_contexts(
        self,
        operation_type: str,
        data_type: str,
        item_data: Dict[str, Any],
        user_id: str,
    ) -> List[str]:
        """Determine which medical contexts are affected by the operation"""

        affected = []

        if data_type == "medication":
            affected.extend(["drug_interactions", "side_effects", "contraindications"])

            # If medication is being discontinued/deleted
            if operation_type in ["delete", "status_change"]:
                if not self.temporal_context.is_medication_active(item_data):
                    affected.append("historical_medications")

            # Check for drug interactions with other active medications
            active_meds = await self._get_active_medications(user_id)
            if len(active_meds) > 1:
                affected.append("multi_drug_analysis")

        elif data_type == "symptom":
            affected.extend(["symptom_patterns", "medication_effectiveness"])

            # Check if symptom is related to known medication side effects
            symptom_name = item_data.get("symptom", "").lower()
            if any(
                keyword in symptom_name
                for keyword in ["nausea", "dizziness", "rash", "fatigue"]
            ):
                affected.append("medication_side_effects")

        elif data_type == "lab_result":
            affected.extend(["health_trends", "medication_monitoring"])

            # Specific lab types affect different contexts
            lab_type = item_data.get("reading_type", "").lower()
            if "glucose" in lab_type or "a1c" in lab_type:
                affected.append("diabetes_management")
            elif "cholesterol" in lab_type or "lipid" in lab_type:
                affected.append("cardiovascular_risk")

        return affected

    async def _get_active_medications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get currently active medications for a user using async queries"""
        try:
            # Use async SQLAlchemy query following the MedicalAIService pattern
            medications_result = await self.db.execute(
                select(Medication)
                .filter(
                    Medication.user_id == user_id,
                    Medication.status == MedicationStatus.ACTIVE,
                )
                .order_by(Medication.start_date.desc())
            )
            medications = medications_result.scalars().all()

            active_meds = []
            for med in medications:
                med_data = {
                    "name": med.name,
                    "status": med.status.value if med.status else "active",
                    "start_date": (
                        med.start_date.isoformat() if med.start_date else None
                    ),
                    "end_date": med.end_date.isoformat() if med.end_date else None,
                    "frequency_details": med.frequency_details,
                }

                if self.temporal_context.is_medication_active(med_data):
                    active_meds.append(med_data)

            return active_meds

        except Exception as e:
            logger.error(f"Error getting active medications: {e}")
            return []

    async def _get_recent_symptoms(
        self, user_id: str, days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get recent symptoms for a user using async queries"""
        try:
            cutoff_date = self.clock.now() - timedelta(days=days)
            symptoms_result = await self.db.execute(
                select(Symptom)
                .filter(
                    Symptom.user_id == user_id, Symptom.reported_date >= cutoff_date
                )
                .order_by(Symptom.reported_date.desc())
                .limit(20)
            )
            symptoms = symptoms_result.scalars().all()

            return [
                {
                    "symptom": symptom.symptom,
                    "severity": symptom.severity.value if symptom.severity else None,
                    "date_time": (
                        symptom.reported_date.isoformat()
                        if symptom.reported_date
                        else None
                    ),
                    "notes": symptom.notes,
                }
                for symptom in symptoms
            ]

        except Exception as e:
            logger.error(f"Error getting recent symptoms: {e}")
            return []

    async def _get_recent_lab_results(
        self, user_id: str, days: int = 180
    ) -> List[Dict[str, Any]]:
        """Get recent lab results for a user using async queries"""
        try:
            cutoff_date = self.clock.now() - timedelta(days=days)
            readings_result = await self.db.execute(
                select(HealthReading)
                .filter(
                    HealthReading.user_id == user_id,
                    HealthReading.reading_date >= cutoff_date,
                )
                .order_by(HealthReading.reading_date.desc())
                .limit(30)
            )
            readings = readings_result.scalars().all()

            return [
                {
                    "reading_type": (
                        reading.reading_type.value
                        if reading.reading_type
                        else "Unknown"
                    ),
                    "numeric_value": (
                        float(reading.numeric_value) if reading.numeric_value else None
                    ),
                    "text_value": reading.text_value,
                    "unit": reading.unit,
                    "date_time": (
                        reading.reading_date.isoformat()
                        if reading.reading_date
                        else None
                    ),
                }
                for reading in readings
            ]

        except Exception as e:
            logger.error(f"Error getting recent lab results: {e}")
            return []

    def _determine_reprocessing_strategy(
        self,
        operation_type: str,
        data_type: str,
        item_data: Dict[str, Any],
        affected_contexts: List[str],
    ) -> str:
        """Determine the appropriate reprocessing strategy"""

        # High-impact operations require full reprocessing
        if (
            "drug_interactions" in affected_contexts
            and operation_type in ["create", "delete"]
            and data_type == "medication"
        ):
            return "full_interaction_analysis"

        # Status changes for medications
        if operation_type == "status_change" and data_type == "medication":
            if not self.temporal_context.is_medication_active(item_data):
                return "historical_context_update"
            else:
                return "activation_context_update"

        # Symptom-related changes
        if data_type == "symptom":
            if "medication_side_effects" in affected_contexts:
                return "side_effect_correlation_analysis"
            else:
                return "symptom_pattern_analysis"

        # Lab results
        if data_type == "lab_result":
            return "trend_analysis"

        # Default to incremental update
        return "incremental_update"

    async def _execute_reprocessing_strategy(
        self,
        strategy: str,
        current_profile: Dict[str, Any],
        item_data: Dict[str, Any],
        affected_contexts: List[str],
    ) -> Dict[str, Any]:
        """Execute the determined reprocessing strategy"""

        try:
            if strategy == "full_interaction_analysis":
                return await self._full_interaction_reanalysis(
                    current_profile, item_data
                )

            elif strategy == "historical_context_update":
                return await self._update_historical_context(current_profile, item_data)

            elif strategy == "activation_context_update":
                return await self._update_activation_context(current_profile, item_data)

            elif strategy == "side_effect_correlation_analysis":
                return await self._analyze_side_effect_correlations(
                    current_profile, item_data
                )

            elif strategy == "symptom_pattern_analysis":
                return await self._analyze_symptom_patterns(current_profile, item_data)

            elif strategy == "trend_analysis":
                return await self._analyze_health_trends(current_profile, item_data)

            else:  # incremental_update
                return await self._incremental_context_update(
                    current_profile, item_data
                )

        except Exception as e:
            logger.error(f"Error executing reprocessing strategy {strategy}: {e}")
            return {"error": str(e)}

    async def _full_interaction_reanalysis(
        self, current_profile: Dict[str, Any], item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform full drug interaction analysis"""

        logger.info("Performing full drug interaction reanalysis")

        # Get all active medications
        active_medications = current_profile.get("medications", [])

        # Filter to only active medications
        truly_active_meds = []
        for med in active_medications:
            if self.temporal_context.is_medication_active(med):
                relevance = self.temporal_context.get_medical_relevance_score(
                    med, "medication"
                )
                med["relevance_score"] = relevance
                truly_active_meds.append(med)

        # Create analysis prompt
        prompt = f"""
        COMPREHENSIVE DRUG INTERACTION ANALYSIS
        
        ACTIVE MEDICATIONS:
        {json.dumps(truly_active_meds, indent=2)}
        
        RECENT CHANGE:
        {json.dumps(item_data, indent=2)}
        
        Please analyze:
        1. All potential drug interactions among active medications
        2. Impact of the recent change on existing interactions
        3. New interaction risks introduced
        4. Recommendations for monitoring or timing adjustments
        5. Any medications that should be discontinued due to interactions
        
        Consider temporal relevance - recently expired medications have lower interaction priority.
        
        Respond in JSON format with detailed interaction analysis.
        """

        # This would call your Gemini service
        gemini_service = get_gemini_service()
        ai_response = await gemini_service.analyze_drug_interactions(truly_active_meds)

        return {
            "analysis_type": "full_interaction_analysis",
            "active_medications_count": len(truly_active_meds),
            "ai_analysis": ai_response,
            "context_updated": True,
        }

    async def _update_historical_context(
        self, current_profile: Dict[str, Any], item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update historical context when medication becomes inactive"""

        logger.info("Updating historical medical context")

        # Move from active to historical context
        # This would update vector embeddings to reduce the weight of this medication
        # in current medical analysis while preserving it for historical reference

        return {
            "analysis_type": "historical_context_update",
            "action": "moved_to_historical",
            "medication": item_data.get("name"),
            "relevance_score": self.temporal_context.get_medical_relevance_score(
                item_data, "medication"
            ),
            "context_updated": True,
        }

    async def _build_current_medical_profile(self, user_id: str) -> Dict[str, Any]:
        """Build current medical profile with temporal awareness using async queries"""

        try:
            # Get medications with temporal filtering
            medications = await self._get_active_medications(user_id)

            # Add relevance scores
            for med in medications:
                med["relevance_score"] = (
                    self.temporal_context.get_medical_relevance_score(med, "medication")
                )

            # Get recent symptoms (last 90 days)
            recent_symptoms = await self._get_recent_symptoms(user_id, days=90)

            # Get recent lab results (last 180 days)
            recent_labs = await self._get_recent_lab_results(user_id, days=180)

            return {
                "user_id": user_id,
                "medications": medications,
                "recent_symptoms": recent_symptoms,
                "recent_labs": recent_labs,
                "profile_timestamp": self.clock.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error building medical profile: {e}")
            return {"user_id": user_id, "error": str(e)}

    # Additional strategy methods would be implemented similarly...
    async def _update_activation_context(self, current_profile, item_data):
        """Handle medication activation - when a medication becomes active again"""
        logger.info("Handling medication activation context update")

        try:
            # Get medication name for analysis
            med_name = item_data.get("name", "Unknown medication")

            # Check for potential interactions with newly active medication
            active_medications = current_profile.get("medications", [])

            # Create focused prompt for activation analysis
            prompt = f"""
            MEDICATION ACTIVATION ANALYSIS
            
            NEWLY ACTIVATED MEDICATION:
            {json.dumps(item_data, indent=2)}
            
            CURRENT ACTIVE MEDICATIONS:
            {json.dumps(active_medications, indent=2)}
            
            Please analyze:
            1. Potential drug interactions with the newly activated medication
            2. Timing considerations for taking this medication with others
            3. Monitoring recommendations for the combination
            4. Any lifestyle or dietary considerations
            
            Respond in JSON format with activation-specific recommendations.
            """

            # Use Gemini for analysis
            gemini_service = get_gemini_service()
            ai_response = await gemini_service.analyze_medical_situation(prompt)

            return {
                "analysis_type": "activation_context_update",
                "medication": med_name,
                "active_medications_count": len(active_medications),
                "ai_analysis": ai_response,
                "context_updated": True,
            }

        except Exception as e:
            logger.error(f"Error in activation context update: {e}")
            return {"analysis_type": "activation_context_update", "error": str(e)}

    async def _analyze_side_effect_correlations(self, current_profile, item_data):
        """Analyze symptom-medication correlations for potential side effects"""
        logger.info("Analyzing side effect correlations")

        try:
            symptom_name = item_data.get(
                "symptom", item_data.get("description", "Unknown symptom")
            )
            symptom_date = item_data.get("date_time", item_data.get("date"))

            # Get medications that could cause this symptom
            active_medications = current_profile.get("medications", [])
            recent_medications = [
                med
                for med in active_medications
                if self.temporal_context.get_medical_relevance_score(med, "medication")
                > 0.5
            ]

            # Create analysis prompt
            prompt = f"""
            SIDE EFFECT CORRELATION ANALYSIS
            
            REPORTED SYMPTOM:
            Name: {symptom_name}
            Date: {symptom_date}
            Additional Details: {json.dumps(item_data, indent=2)}
            
            CURRENT/RECENT MEDICATIONS:
            {json.dumps(recent_medications, indent=2)}
            
            Please analyze:
            1. Which medications could potentially cause this symptom as a side effect
            2. Timeline correlation between medication start dates and symptom onset
            3. Severity assessment - is this a common or rare side effect
            4. Recommendations for monitoring or medication adjustment
            5. When to contact healthcare provider
            
            Respond in JSON format with correlation analysis and recommendations.
            """

            # Use Gemini for analysis
            gemini_service = get_gemini_service()
            ai_response = await gemini_service.analyze_symptoms_with_medications(
                [item_data], recent_medications
            )

            return {
                "analysis_type": "side_effect_correlation_analysis",
                "symptom": symptom_name,
                "medications_analyzed": len(recent_medications),
                "ai_analysis": ai_response,
                "context_updated": True,
            }

        except Exception as e:
            logger.error(f"Error in side effect correlation analysis: {e}")
            return {
                "analysis_type": "side_effect_correlation_analysis",
                "error": str(e),
            }

    async def _analyze_symptom_patterns(self, current_profile, item_data):
        """Analyze symptom patterns and trends over time"""
        logger.info("Analyzing symptom patterns")

        try:
            current_symptom = item_data.get("symptom", item_data.get("description"))

            # Get recent symptoms for pattern analysis
            recent_symptoms = current_profile.get("recent_symptoms", [])

            # Filter to symptoms in the last 90 days
            relevant_symptoms = []
            cutoff_date = self.clock.today() - timedelta(days=90)

            for symptom in recent_symptoms:
                symptom_date_str = symptom.get("date_time", symptom.get("date"))
                if symptom_date_str:
                    try:
                        symptom_date = datetime.fromisoformat(
                            symptom_date_str.replace("Z", "+00:00")
                        ).date()
                        if symptom_date >= cutoff_date:
                            relevant_symptoms.append(symptom)
                    except:
                        continue

            # Create pattern analysis prompt
            prompt = f"""
            SYMPTOM PATTERN ANALYSIS
            
            CURRENT SYMPTOM EVENT:
            {json.dumps(item_data, indent=2)}
            
            RECENT SYMPTOM HISTORY (90 days):
            {json.dumps(relevant_symptoms, indent=2)}
            
            Please analyze:
            1. Recurring patterns in symptom occurrence
            2. Potential triggers or correlations with activities/medications
            3. Severity trends over time
            4. Clustering of symptoms that might indicate underlying conditions
            5. Recommendations for symptom tracking or medical consultation
            
            Respond in JSON format with pattern analysis and insights.
            """

            # Use Gemini for analysis
            gemini_service = get_gemini_service()
            ai_response = await gemini_service.analyze_medical_situation(prompt)

            return {
                "analysis_type": "symptom_pattern_analysis",
                "current_symptom": current_symptom,
                "symptoms_analyzed": len(relevant_symptoms),
                "ai_analysis": ai_response,
                "context_updated": True,
            }

        except Exception as e:
            logger.error(f"Error in symptom pattern analysis: {e}")
            return {"analysis_type": "symptom_pattern_analysis", "error": str(e)}

    async def _analyze_health_trends(self, current_profile, item_data):
        """Analyze health trends from lab results and vital signs"""
        logger.info("Analyzing health trends")

        try:
            current_reading_type = item_data.get(
                "reading_type", item_data.get("test_type")
            )
            current_value = item_data.get("numeric_value", item_data.get("value"))

            # Get recent lab results/health readings
            recent_labs = current_profile.get("recent_labs", [])

            # Filter to same type of readings for trend analysis
            same_type_readings = []
            for lab in recent_labs:
                if (
                    lab.get("reading_type") == current_reading_type
                    or lab.get("test_type") == current_reading_type
                ):
                    same_type_readings.append(lab)

            # Sort by date for trend analysis
            same_type_readings.sort(key=lambda x: x.get("date_time", x.get("date", "")))

            # Create trend analysis prompt
            prompt = f"""
            HEALTH TREND ANALYSIS
            
            CURRENT READING:
            {json.dumps(item_data, indent=2)}
            
            HISTORICAL READINGS (Same Type):
            {json.dumps(same_type_readings, indent=2)}
            
            Please analyze:
            1. Trend direction (improving, worsening, stable)
            2. Rate of change and clinical significance
            3. Comparison to normal reference ranges
            4. Potential impact of current medications on these values
            5. Recommendations for follow-up testing or lifestyle changes
            6. When to alert healthcare provider about concerning trends
            
            Respond in JSON format with trend analysis and clinical insights.
            """

            # Use Gemini for analysis
            gemini_service = get_gemini_service()
            ai_response = await gemini_service.analyze_lab_trends(
                same_type_readings + [item_data]
            )

            return {
                "analysis_type": "trend_analysis",
                "reading_type": current_reading_type,
                "current_value": current_value,
                "historical_points": len(same_type_readings),
                "ai_analysis": ai_response,
                "context_updated": True,
            }

        except Exception as e:
            logger.error(f"Error in health trend analysis: {e}")
            return {"analysis_type": "trend_analysis", "error": str(e)}

    async def _incremental_context_update(self, current_profile, item_data):
        """Perform incremental context update for low-impact changes"""
        logger.info("Performing incremental context update")

        try:
            # Determine the type of data and minimal processing needed
            data_keys = item_data.keys()

            # Simple logging and minimal processing for low-impact changes
            impact_assessment = {
                "change_type": "incremental",
                "fields_changed": list(data_keys),
                "processing_needed": "minimal",
                "context_updated": True,
            }

            # For incremental updates, we mainly log and update timestamps
            # without expensive AI analysis
            logger.info(f"Incremental update processed for fields: {list(data_keys)}")

            return {
                "analysis_type": "incremental_update",
                "impact_assessment": impact_assessment,
                "processing_time": "minimal",
                "context_updated": True,
            }

        except Exception as e:
            logger.error(f"Error in incremental context update: {e}")
            return {"analysis_type": "incremental_update", "error": str(e)}


class SelectiveReprocessingService:
    """Service for selectively reprocessing only changed fields with CRUD operation support."""

    def __init__(self, clock_provider: ClockProvider = None, gemini_service=None):
        self.clock = clock_provider or SystemClockProvider()
        self.gemini_service = gemini_service or get_gemini_service()
        self.extracted_data_repo = ExtractedDataRepository(ExtractedData)

    async def handle_crud_operation(
        self,
        db: AsyncSession,
        operation_type: str,
        data_type: str,
        item_data: Dict[str, Any],
        user_id: str,
        affected_documents: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle CRUD operations with intelligent reprocessing

        Args:
            db: Async database session
            operation_type: 'create', 'update', 'delete', 'status_change'
            data_type: 'medication', 'symptom', 'lab_result', 'health_reading'
            item_data: The data that was changed
            user_id: User ID
            affected_documents: Optional list of document IDs that might be affected

        Returns:
            Dictionary with reprocessing results
        """
        crud_handler = CRUDOperationHandler(db, self.clock)
        return await crud_handler.handle_crud_operation(
            operation_type, data_type, item_data, user_id, affected_documents
        )

    async def reprocess_changed_fields(
        self,
        db: Session,
        document_id: str,
        changed_fields: List[Dict[str, Any]],
        current_content: Any,
        raw_text: Optional[str] = None,
    ) -> Any:
        """
        Reprocess only the fields that were changed by the user.

        Implementation Strategy:
        1. Group changes by section/context
        2. Extract relevant text context for each section
        3. Use focused AI prompts for each changed section
        4. Merge results back into the content while preserving unchanged data

        Args:
            db: Database session
            document_id: ID of the document
            changed_fields: List of fields that were changed
            current_content: Current content with user corrections
            raw_text: Original OCR text for context

        Returns:
            Updated content with AI suggestions for related fields
        """
        try:
            logger.info(f"Starting selective reprocessing for document {document_id}")
            logger.info(f"Processing {len(changed_fields)} changed fields")

            if not changed_fields or not raw_text:
                logger.info("No changes to process or no raw text available")
                return current_content

            # Step 1: Group changes by section and context
            grouped_changes = self._group_changes_by_context(changed_fields)
            logger.info(f"Grouped changes into {len(grouped_changes)} contexts")

            # Step 2: Process each context group
            updated_content = (
                current_content.copy()
                if isinstance(current_content, dict)
                else current_content
            )

            for context, changes in grouped_changes.items():
                logger.info(
                    f"Processing context: {context} with {len(changes)} changes"
                )

                # Extract relevant text for this context
                context_text = self._extract_context_text(raw_text, context, changes)

                if context_text:
                    # Generate focused AI reprocessing for this context
                    ai_suggestions = await self._generate_context_specific_suggestions(
                        context, changes, context_text, current_content
                    )

                    if ai_suggestions:
                        # Merge AI suggestions with current content
                        updated_content = self._merge_ai_suggestions(
                            updated_content, ai_suggestions, context, changes
                        )

            logger.info(f"Selective reprocessing completed for document {document_id}")
            return updated_content

        except Exception as e:
            logger.error(
                f"Error in selective reprocessing for document {document_id}: {e}",
                exc_info=True,
            )
            return current_content

    def _group_changes_by_context(
        self, changed_fields: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group changes by logical context (medications, lab_results, etc.)
        """
        grouped = {}

        for change in changed_fields:
            section = change.get("section", "general")

            # Determine context grouping
            context = self._determine_context(section, change)

            if context not in grouped:
                grouped[context] = []
            grouped[context].append(change)

        return grouped

    def _determine_context(self, section: str, change: Dict[str, Any]) -> str:
        """
        Determine the processing context for a change
        """
        # Map sections to processing contexts
        context_mapping = {
            "medications": "medication_analysis",
            "lab_results": "lab_analysis",
            "medical_events": "clinical_analysis",
            "extracted_metadata": "metadata_analysis",
        }

        return context_mapping.get(section, "general_analysis")

    def _extract_context_text(
        self, raw_text: str, context: str, changes: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Extract relevant portions of raw text for the given context
        """
        try:
            # Keywords to look for based on context
            context_keywords = {
                "medication_analysis": [
                    "medication",
                    "drug",
                    "prescription",
                    "dose",
                    "dosage",
                    "mg",
                    "ml",
                    "tablet",
                    "capsule",
                    "daily",
                    "twice",
                    "morning",
                    "evening",
                    "take",
                    "prescribed",
                    "rx",
                    "refill",
                ],
                "lab_analysis": [
                    "lab",
                    "test",
                    "result",
                    "blood",
                    "urine",
                    "glucose",
                    "cholesterol",
                    "hemoglobin",
                    "white",
                    "red",
                    "count",
                    "level",
                    "mg/dl",
                    "mmol/l",
                    "normal",
                    "abnormal",
                    "high",
                    "low",
                    "range",
                ],
                "clinical_analysis": [
                    "diagnosis",
                    "symptom",
                    "condition",
                    "patient",
                    "history",
                    "physical",
                    "examination",
                    "assessment",
                    "plan",
                    "treatment",
                ],
                "metadata_analysis": [
                    "date",
                    "doctor",
                    "physician",
                    "clinic",
                    "hospital",
                    "patient",
                    "name",
                    "dob",
                    "address",
                    "phone",
                ],
            }

            keywords = context_keywords.get(context, [])

            # Extract sentences containing relevant keywords
            sentences = raw_text.split(".")
            relevant_sentences = []

            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword.lower() in sentence.lower() for keyword in keywords):
                    relevant_sentences.append(sentence)

            # Also include sentences with field values that were changed
            for change in changes:
                old_value = str(change.get("oldValue", "")).strip()
                new_value = str(change.get("newValue", "")).strip()

                for sentence in sentences:
                    if old_value and old_value.lower() in sentence.lower():
                        if sentence not in relevant_sentences:
                            relevant_sentences.append(sentence)

            if relevant_sentences:
                context_text = ". ".join(relevant_sentences)
                logger.info(
                    f"Extracted {len(relevant_sentences)} relevant sentences for context {context}"
                )
                return context_text

            return None

        except Exception as e:
            logger.error(f"Error extracting context text: {e}")
            return None

    async def _generate_context_specific_suggestions(
        self,
        context: str,
        changes: List[Dict[str, Any]],
        context_text: str,
        current_content: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate AI suggestions for a specific context
        """
        try:
            prompt = self._build_focused_prompt(
                context, changes, context_text, current_content
            )

            if not prompt:
                return None

            # Use Gemini for focused analysis
            ai_response = await self.gemini_service.analyze_medical_situation(prompt)

            if ai_response:
                # Parse the AI response
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback: try to extract JSON from response
                    return self._extract_json_from_response(ai_response)

            return None

        except Exception as e:
            logger.error(f"Error generating AI suggestions for context {context}: {e}")
            return None

    def _build_focused_prompt(
        self,
        context: str,
        changes: List[Dict[str, Any]],
        context_text: str,
        current_content: Any,
    ) -> Optional[str]:
        """
        Build a focused prompt for the specific context
        """
        try:
            # Context-specific prompt templates
            prompt_templates = {
                "medication_analysis": self._build_medication_prompt,
                "lab_analysis": self._build_lab_prompt,
                "clinical_analysis": self._build_clinical_prompt,
                "metadata_analysis": self._build_metadata_prompt,
            }

            prompt_builder = prompt_templates.get(context)
            if prompt_builder:
                return prompt_builder(changes, context_text, current_content)

            return None

        except Exception as e:
            logger.error(f"Error building prompt for context {context}: {e}")
            return None

    def _build_medication_prompt(
        self, changes: List[Dict[str, Any]], context_text: str, current_content: Any
    ) -> str:
        """Build focused prompt for medication-related changes"""

        change_summary = []
        for change in changes:
            change_summary.append(
                f"- Field '{change.get('field')}' changed from '{change.get('oldValue')}' to '{change.get('newValue')}'"
            )

        return f"""
        You are analyzing medication information from a medical document. A user has made corrections to extracted data.

        ORIGINAL TEXT CONTEXT:
        {context_text}

        USER CORRECTIONS MADE:
        {chr(10).join(change_summary)}

        CURRENT EXTRACTED MEDICATIONS:
        {json.dumps(current_content.get('medical_events', []) if isinstance(current_content, dict) else [], indent=2)}

        Based on the user corrections and the original text, suggest improvements to OTHER medication-related fields that might also need updating. Focus on:
        1. Dosage information that might be related
        2. Frequency details that might need adjustment
        3. Additional medication properties that could be extracted
        4. Cross-references between medications

        Respond with JSON format:
        {{
            "suggestions": [
                {{
                    "section": "medications",
                    "index": 0,
                    "field": "dosage",
                    "current_value": "current_value",
                    "suggested_value": "suggested_value",
                    "confidence": 0.8,
                    "reason": "explanation for suggestion"
                }}
            ],
            "confidence": 0.7
        }}
        """

    def _build_lab_prompt(
        self, changes: List[Dict[str, Any]], context_text: str, current_content: Any
    ) -> str:
        """Build focused prompt for lab result changes"""

        change_summary = []
        for change in changes:
            change_summary.append(
                f"- Field '{change.get('field')}' changed from '{change.get('oldValue')}' to '{change.get('newValue')}'"
            )

        return f"""
        You are analyzing laboratory results from a medical document. A user has made corrections to extracted data.

        ORIGINAL TEXT CONTEXT:
        {context_text}

        USER CORRECTIONS MADE:
        {chr(10).join(change_summary)}

        CURRENT EXTRACTED LAB RESULTS:
        {json.dumps(current_content.get('medical_events', []) if isinstance(current_content, dict) else [], indent=2)}

        Based on the user corrections and the original text, suggest improvements to OTHER lab-related fields. Focus on:
        1. Units that might need correction
        2. Reference ranges that could be extracted
        3. Related lab values that might be present
        4. Date/time information for lab results

        Respond with JSON format:
        {{
            "suggestions": [
                {{
                    "section": "lab_results",
                    "index": 0,
                    "field": "units",
                    "current_value": "current_value",
                    "suggested_value": "suggested_value",
                    "confidence": 0.9,
                    "reason": "explanation for suggestion"
                }}
            ],
            "confidence": 0.8
        }}
        """

    def _build_clinical_prompt(
        self, changes: List[Dict[str, Any]], context_text: str, current_content: Any
    ) -> str:
        """Build focused prompt for clinical information changes"""

        change_summary = []
        for change in changes:
            change_summary.append(
                f"- Field '{change.get('field')}' changed from '{change.get('oldValue')}' to '{change.get('newValue')}'"
            )

        return f"""
        You are analyzing clinical information from a medical document. A user has made corrections to extracted data.

        ORIGINAL TEXT CONTEXT:
        {context_text}

        USER CORRECTIONS MADE:
        {chr(10).join(change_summary)}

        CURRENT EXTRACTED CLINICAL DATA:
        {json.dumps(current_content.get('medical_events', []) if isinstance(current_content, dict) else [], indent=2)}

        Based on the user corrections and the original text, suggest improvements to OTHER clinical fields. Focus on:
        1. Symptoms that might be related
        2. Diagnoses that could be better extracted
        3. Treatment plans or recommendations
        4. Medical history information

        Respond with JSON format:
        {{
            "suggestions": [
                {{
                    "section": "medical_events",
                    "index": 0,
                    "field": "description",
                    "current_value": "current_value",
                    "suggested_value": "suggested_value",
                    "confidence": 0.7,
                    "reason": "explanation for suggestion"
                }}
            ],
            "confidence": 0.6
        }}
        """

    def _build_metadata_prompt(
        self, changes: List[Dict[str, Any]], context_text: str, current_content: Any
    ) -> str:
        """Build focused prompt for metadata changes"""

        change_summary = []
        for change in changes:
            change_summary.append(
                f"- Field '{change.get('field')}' changed from '{change.get('oldValue')}' to '{change.get('newValue')}'"
            )

        return f"""
        You are analyzing document metadata from a medical document. A user has made corrections to extracted data.

        ORIGINAL TEXT CONTEXT:
        {context_text}

        USER CORRECTIONS MADE:
        {chr(10).join(change_summary)}

        CURRENT EXTRACTED METADATA:
        {json.dumps(current_content.get('extracted_metadata', {}) if isinstance(current_content, dict) else {}, indent=2)}

        Based on the user corrections and the original text, suggest improvements to OTHER metadata fields. Focus on:
        1. Document dates that might need correction
        2. Source information (doctor, clinic names)
        3. Location information
        4. Document tags or categories

        Respond with JSON format:
        {{
            "suggestions": [
                {{
                    "section": "extracted_metadata",
                    "field": "document_date",
                    "current_value": "current_value",
                    "suggested_value": "suggested_value",
                    "confidence": 0.9,
                    "reason": "explanation for suggestion"
                }}
            ],
            "confidence": 0.8
        }}
        """

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from AI response that might contain additional text
        """
        try:
            # Look for JSON block in response
            start_idx = response.find("{")
            end_idx = response.rfind("}")

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx : end_idx + 1]
                return json.loads(json_str)

            return None

        except Exception:
            return None

    def _merge_ai_suggestions(
        self,
        current_content: Any,
        ai_suggestions: Dict[str, Any],
        context: str,
        changes: List[Dict[str, Any]],
    ) -> Any:
        """
        Merge AI suggestions with current content
        """
        try:
            if not isinstance(current_content, dict) or not ai_suggestions.get(
                "suggestions"
            ):
                return current_content

            updated_content = current_content.copy()
            suggestions = ai_suggestions.get("suggestions", [])

            # Apply high-confidence suggestions
            high_confidence_threshold = 0.8

            for suggestion in suggestions:
                confidence = suggestion.get("confidence", 0.0)

                if confidence >= high_confidence_threshold:
                    section = suggestion.get("section")
                    field = suggestion.get("field")
                    suggested_value = suggestion.get("suggested_value")

                    # Apply suggestion based on section
                    if section == "extracted_metadata":
                        if "extracted_metadata" not in updated_content:
                            updated_content["extracted_metadata"] = {}
                        updated_content["extracted_metadata"][field] = suggested_value

                    elif section in ["medications", "lab_results", "medical_events"]:
                        if "medical_events" not in updated_content:
                            updated_content["medical_events"] = []

                        # Find the specific item to update
                        index = suggestion.get("index", 0)
                        if 0 <= index < len(updated_content["medical_events"]):
                            updated_content["medical_events"][index][
                                field
                            ] = suggested_value

                    logger.info(
                        f"Applied AI suggestion: {section}.{field} = {suggested_value} (confidence: {confidence})"
                    )

            # Log lower confidence suggestions for review
            for suggestion in suggestions:
                confidence = suggestion.get("confidence", 0.0)
                if confidence < high_confidence_threshold:
                    reason = suggestion.get("reason", "No reason provided")
                    logger.info(
                        f"Low confidence suggestion not applied: {suggestion.get('section')}.{suggestion.get('field')} - {reason} (confidence: {confidence})"
                    )

            return updated_content

        except Exception as e:
            logger.error(f"Error merging AI suggestions: {e}")
            return current_content
