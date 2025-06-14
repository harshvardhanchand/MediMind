"""
Auto-Population Service
Converts extracted medical events from documents into structured database entries
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models.medication import Medication, MedicationStatus, MedicationFrequency
from app.models.symptom import Symptom, SymptomSeverity
from app.models.health_reading import HealthReading, HealthReadingType
from app.models.extracted_data import ExtractedData
from app.repositories.medication_repo import medication_repo
from app.repositories.symptom_repo import symptom_repo
from app.repositories.health_reading_repo import health_reading_repo
from app.schemas.medication import MedicationCreate
from app.schemas.symptom import SymptomCreate
from app.schemas.health_reading import HealthReadingCreate

logger = logging.getLogger(__name__)

class AutoPopulationService:
    """
    Service for automatically populating structured tables from extracted medical events
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Mapping for medication frequencies
        self.frequency_mapping = {
            "once daily": MedicationFrequency.ONCE_DAILY,
            "twice daily": MedicationFrequency.TWICE_DAILY,
            "three times daily": MedicationFrequency.THREE_TIMES_DAILY,
            "four times daily": MedicationFrequency.FOUR_TIMES_DAILY,
            "once a day": MedicationFrequency.ONCE_DAILY,
            "twice a day": MedicationFrequency.TWICE_DAILY,
            "bid": MedicationFrequency.TWICE_DAILY,
            "tid": MedicationFrequency.THREE_TIMES_DAILY,
            "qid": MedicationFrequency.FOUR_TIMES_DAILY,
            "daily": MedicationFrequency.ONCE_DAILY,
            "weekly": MedicationFrequency.ONCE_WEEKLY,
            "once weekly": MedicationFrequency.ONCE_WEEKLY,
            "twice weekly": MedicationFrequency.TWICE_WEEKLY,
            "monthly": MedicationFrequency.ONCE_MONTHLY,
            "once monthly": MedicationFrequency.ONCE_MONTHLY,
            "every other day": MedicationFrequency.EVERY_OTHER_DAY,
            "as needed": MedicationFrequency.AS_NEEDED,
            "prn": MedicationFrequency.AS_NEEDED,
        }
        
        # Mapping for symptom severities
        self.severity_mapping = {
            "mild": SymptomSeverity.MILD,
            "moderate": SymptomSeverity.MODERATE,
            "severe": SymptomSeverity.SEVERE,
            "low": SymptomSeverity.MILD,
            "medium": SymptomSeverity.MODERATE,
            "high": SymptomSeverity.SEVERE,
        }
        
        # Mapping for health reading types
        self.health_reading_mapping = {
            "blood pressure": HealthReadingType.BLOOD_PRESSURE,
            "systolic": HealthReadingType.BLOOD_PRESSURE,
            "diastolic": HealthReadingType.BLOOD_PRESSURE,
            "glucose": HealthReadingType.GLUCOSE,
            "blood sugar": HealthReadingType.GLUCOSE,
            "fasting glucose": HealthReadingType.GLUCOSE,
            "fasting blood sugar": HealthReadingType.GLUCOSE,
            "cholesterol": HealthReadingType.OTHER,
            "total cholesterol": HealthReadingType.OTHER,
            "hdl": HealthReadingType.OTHER,
            "ldl": HealthReadingType.OTHER,
            "weight": HealthReadingType.WEIGHT,
            "height": HealthReadingType.HEIGHT,
            "bmi": HealthReadingType.BMI,
            "heart rate": HealthReadingType.HEART_RATE,
            "pulse": HealthReadingType.HEART_RATE,
            "temperature": HealthReadingType.TEMPERATURE,
            "spo2": HealthReadingType.SPO2,
            "oxygen saturation": HealthReadingType.SPO2,
            "respiratory rate": HealthReadingType.RESPIRATORY_RATE,
            "pain level": HealthReadingType.PAIN_LEVEL,
            "steps": HealthReadingType.STEPS,
            "sleep": HealthReadingType.SLEEP,
            "hemoglobin": HealthReadingType.OTHER,
            "hba1c": HealthReadingType.OTHER,
            "creatinine": HealthReadingType.OTHER,
        }
    
    async def populate_from_extracted_data(
        self, 
        user_id: str, 
        extracted_data: ExtractedData,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Main method to populate structured tables from extracted medical events
        
        Returns:
            Dict with counts of created entries and any errors
        """
        logger.info(f"Starting auto-population for user {user_id}, document {document_id}")
        
        result = {
            "medications_created": 0,
            "symptoms_created": 0,
            "health_readings_created": 0,
            "errors": [],
            "skipped_duplicates": 0
        }
        
        if not extracted_data.content or not isinstance(extracted_data.content, list):
            logger.warning(f"No valid medical events found in extracted data for document {document_id}")
            return result
        
        for event in extracted_data.content:
            try:
                event_type = event.get("event_type", "").lower()
                
                if event_type == "medication":
                    created = await self._create_medication_from_event(user_id, event, document_id)
                    if created:
                        result["medications_created"] += 1
                    else:
                        result["skipped_duplicates"] += 1
                        
                elif event_type == "symptom":
                    created = await self._create_symptom_from_event(user_id, event, document_id)
                    if created:
                        result["symptoms_created"] += 1
                    else:
                        result["skipped_duplicates"] += 1
                        
                elif event_type in ["labresult", "lab_result", "vitalsign", "vital_sign"]:
                    created = await self._create_health_reading_from_event(user_id, event, document_id)
                    if created:
                        result["health_readings_created"] += 1
                    else:
                        result["skipped_duplicates"] += 1
                        
                else:
                    logger.debug(f"Skipping event type '{event_type}' - not supported for auto-population")
                    
            except Exception as e:
                error_msg = f"Failed to process event {event.get('description', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
        
        logger.info(f"Auto-population completed: {result}")
        return result
    
    async def _create_medication_from_event(
        self, 
        user_id: str, 
        event: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """Create medication entry from extracted event"""
        try:
            medication_name = event.get("description", "").strip()
            if not medication_name:
                logger.warning("Skipping medication with empty name")
                return False
            
            # Check for duplicates
            if self._is_duplicate_medication(user_id, medication_name):
                logger.info(f"Skipping duplicate medication: {medication_name}")
                return False
            
            # Parse dosage and frequency
            dosage = self._extract_dosage(event)
            frequency = self._extract_frequency(event)
            
            # Parse date
            start_date = self._parse_date(event.get("date_time"))
            
            # Create medication
            medication_data = MedicationCreate(
                name=medication_name,
                dosage=dosage,
                frequency=frequency,
                start_date=start_date,
                status=MedicationStatus.ACTIVE,
                notes=f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}",
                related_document_id=uuid.UUID(document_id) if document_id else None
            )
            
            db_medication = medication_repo.create_with_owner(
                db=self.db,
                obj_in=medication_data,
                user_id=uuid.UUID(user_id)
            )
            
            logger.info(f"Created medication: {medication_name} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create medication from event: {str(e)}")
            return False
    
    async def _create_symptom_from_event(
        self, 
        user_id: str, 
        event: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """Create symptom entry from extracted event"""
        try:
            symptom_name = event.get("description", "").strip()
            if not symptom_name:
                logger.warning("Skipping symptom with empty name")
                return False
            
            # Check for duplicates (within last 7 days)
            if self._is_duplicate_symptom(user_id, symptom_name, event.get("date_time")):
                logger.info(f"Skipping duplicate symptom: {symptom_name}")
                return False
            
            # Parse severity
            severity = self._extract_severity(event)
            
            # Parse date
            reported_date = self._parse_datetime(event.get("date_time"))
            
            # Extract location and notes
            location = event.get("body_location")
            notes = f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}"
            if event.get("notes"):
                notes += f" | Additional notes: {event.get('notes')}"
            
            # Create symptom
            symptom_data = SymptomCreate(
                symptom=symptom_name,
                severity=severity,
                reported_date=reported_date or datetime.utcnow(),
                location=location,
                notes=notes
            )
            
            db_symptom = symptom_repo.create_with_user(
                db=self.db,
                obj_in=symptom_data,
                user_id=uuid.UUID(user_id)
            )
            
            logger.info(f"Created symptom: {symptom_name} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create symptom from event: {str(e)}")
            return False
    
    async def _create_health_reading_from_event(
        self, 
        user_id: str, 
        event: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """Create health reading entry from extracted event"""
        try:
            test_name = event.get("description", "").strip().lower()
            if not test_name:
                logger.warning("Skipping health reading with empty test name")
                return False
            
            # Map to health reading type
            reading_type = self._map_health_reading_type(test_name)
            
            # Parse value and units
            value = event.get("value")
            units = event.get("units")
            
            if not value:
                logger.warning(f"Skipping health reading {test_name} with no value")
                return False
            
            # Check for duplicates
            if self._is_duplicate_health_reading(user_id, reading_type, event.get("date_time")):
                logger.info(f"Skipping duplicate health reading: {test_name}")
                return False
            
            # Parse date
            reading_date = self._parse_datetime(event.get("date_time"))
            
            # Handle special cases (blood pressure)
            systolic_value = None
            diastolic_value = None
            numeric_value = None
            
            if reading_type == HealthReadingType.BLOOD_PRESSURE and "/" in str(value):
                # Parse blood pressure format like "120/80"
                try:
                    bp_parts = str(value).split("/")
                    systolic_value = int(bp_parts[0].strip())
                    diastolic_value = int(bp_parts[1].strip())
                except (ValueError, IndexError):
                    numeric_value = self._parse_numeric_value(value)
            else:
                numeric_value = self._parse_numeric_value(value)
            
            # Create health reading
            health_reading_data = HealthReadingCreate(
                reading_type=reading_type,
                numeric_value=numeric_value,
                systolic_value=systolic_value,
                diastolic_value=diastolic_value,
                unit=units,
                reading_date=reading_date or datetime.utcnow(),
                notes=f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}",
                source="Document Upload",
                related_document_id=uuid.UUID(document_id) if document_id else None
            )
            
            db_health_reading = health_reading_repo.create_with_owner(
                db=self.db,
                obj_in=health_reading_data,
                user_id=uuid.UUID(user_id)
            )
            
            logger.info(f"Created health reading: {test_name} = {value} {units} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create health reading from event: {str(e)}")
            return False
    
    def _extract_dosage(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract dosage from event"""
        value = event.get("value")
        units = event.get("units")
        
        if value and units:
            return f"{value} {units}"
        elif value:
            return str(value)
        
        # Try to extract from qualifiers or description
        qualifiers = event.get("qualifiers", [])
        if isinstance(qualifiers, list):
            for qualifier in qualifiers:
                if any(unit in str(qualifier).lower() for unit in ["mg", "ml", "mcg", "g", "tablet", "capsule"]):
                    return str(qualifier)
        elif isinstance(qualifiers, str):
            if any(unit in qualifiers.lower() for unit in ["mg", "ml", "mcg", "g", "tablet", "capsule"]):
                return qualifiers
        
        return None
    
    def _extract_frequency(self, event: Dict[str, Any]) -> MedicationFrequency:
        """Extract frequency from event"""
        qualifiers = event.get("qualifiers", [])
        
        # Convert to string for searching
        qualifier_text = ""
        if isinstance(qualifiers, list):
            qualifier_text = " ".join(str(q) for q in qualifiers).lower()
        elif isinstance(qualifiers, str):
            qualifier_text = qualifiers.lower()
        
        # Check description and notes too
        description = event.get("description", "").lower()
        notes = event.get("notes", "").lower()
        search_text = f"{qualifier_text} {description} {notes}"
        
        # Find frequency match
        for freq_text, freq_enum in self.frequency_mapping.items():
            if freq_text in search_text:
                return freq_enum
        
        # Default frequency
        return MedicationFrequency.AS_NEEDED
    
    def _extract_severity(self, event: Dict[str, Any]) -> SymptomSeverity:
        """Extract severity from event"""
        qualifiers = event.get("qualifiers", [])
        
        # Convert to string for searching
        qualifier_text = ""
        if isinstance(qualifiers, list):
            qualifier_text = " ".join(str(q) for q in qualifiers).lower()
        elif isinstance(qualifiers, str):
            qualifier_text = qualifiers.lower()
        
        # Check description and notes too
        description = event.get("description", "").lower()
        notes = event.get("notes", "").lower()
        search_text = f"{qualifier_text} {description} {notes}"
        
        # Find severity match
        for severity_text, severity_enum in self.severity_mapping.items():
            if severity_text in search_text:
                return severity_enum
        
        # Default severity
        return SymptomSeverity.MODERATE
    
    def _map_health_reading_type(self, test_name: str) -> HealthReadingType:
        """Map test name to health reading type"""
        test_name_lower = test_name.lower()
        
        for key, reading_type in self.health_reading_mapping.items():
            if key in test_name_lower:
                return reading_type
        
        # Default to OTHER for unrecognized tests
        return HealthReadingType.OTHER
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If no format matches, return today
            logger.warning(f"Could not parse date '{date_str}', using today")
            return date.today()
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different datetime formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return now
            logger.warning(f"Could not parse datetime '{date_str}', using now")
            return datetime.utcnow()
            
        except Exception as e:
            logger.warning(f"Error parsing datetime '{date_str}': {str(e)}")
            return None
    
    def _parse_numeric_value(self, value: Any) -> Optional[float]:
        """Parse numeric value from various formats"""
        if value is None:
            return None
        
        try:
            # Remove common non-numeric characters
            value_str = str(value).strip()
            value_str = value_str.replace(",", "").replace("<", "").replace(">", "")
            
            # Extract first number found
            import re
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                return float(numbers[0])
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def _is_duplicate_medication(self, user_id: str, medication_name: str) -> bool:
        """Check if medication already exists for user"""
        try:
            existing = self.db.query(Medication).filter(
                Medication.user_id == user_id,
                Medication.name.ilike(f"%{medication_name}%"),
                Medication.status == MedicationStatus.ACTIVE
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking medication duplicate: {str(e)}")
            return False
    
    def _is_duplicate_symptom(self, user_id: str, symptom_name: str, event_date: Optional[str]) -> bool:
        """Check if similar symptom exists within last 7 days"""
        try:
            # Parse event date or use current time
            check_date = self._parse_datetime(event_date) or datetime.utcnow()
            cutoff_date = check_date - timedelta(days=7)
            
            existing = self.db.query(Symptom).filter(
                Symptom.user_id == user_id,
                Symptom.symptom.ilike(f"%{symptom_name}%"),
                Symptom.reported_date >= cutoff_date
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking symptom duplicate: {str(e)}")
            return False
    
    def _is_duplicate_health_reading(self, user_id: str, reading_type: HealthReadingType, event_date: Optional[str]) -> bool:
        """Check if similar health reading exists on same day"""
        try:
            # Parse event date or use current time
            check_date = self._parse_datetime(event_date) or datetime.utcnow()
            check_date_only = check_date.date()
            
            existing = self.db.query(HealthReading).filter(
                HealthReading.user_id == user_id,
                HealthReading.reading_type == reading_type,
                HealthReading.reading_date >= check_date_only,
                HealthReading.reading_date < check_date_only + timedelta(days=1)
            ).first()
            
            return existing is not None
            
        except Exception as e:
            logger.error(f"Error checking health reading duplicate: {str(e)}")
            return False


def get_auto_population_service(db: Session) -> AutoPopulationService:
    """Factory function to get auto-population service"""
    return AutoPopulationService(db) 