"""
Auto-Population Service
Converts extracted medical events from documents into structured database entries
"""

import logging
import uuid
import re
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta,timezone
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from dateutil import parser as dateutil_parser

from app.models.medication import Medication, MedicationStatus, MedicationFrequency
from app.models.symptom import Symptom, SymptomSeverity
from app.models.health_reading import HealthReading, HealthReadingType
from app.models.extracted_data import ExtractedData
from app.schemas.medication import MedicationCreate
from app.schemas.symptom import SymptomCreate
from app.schemas.health_reading import HealthReadingCreate

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single event"""
    success: bool
    event_type: str
    event_description: str
    error_message: Optional[str] = None
    was_duplicate: bool = False

@dataclass
class ExistingRecords:
    """Container for existing records used in duplicate detection"""
    medications: Dict[str, Medication]
    symptoms: Dict[Tuple[str, date], Symptom]  
    health_readings: Dict[Tuple[HealthReadingType, date], HealthReading]

class MedicalDataExtractor:
    """Helper class for extracting and parsing medical data from events"""
    
    # Externalized mapping configurations
    FREQUENCY_MAPPING = {
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
    
    SEVERITY_MAPPING = {
        "mild": SymptomSeverity.MILD,
        "moderate": SymptomSeverity.MODERATE,
        "severe": SymptomSeverity.SEVERE,
        "low": SymptomSeverity.MILD,
        "medium": SymptomSeverity.MODERATE,
        "high": SymptomSeverity.SEVERE,
    }
    
    HEALTH_READING_MAPPING = {
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
    
    @staticmethod
    def parse_robust_date(date_str: Optional[str]) -> Optional[date]:
        """Parse date string using dateutil with comprehensive error handling"""
        if not date_str:
            return None
        
        try:
            # Use dateutil parser for robust date parsing
            parsed_dt = dateutil_parser.parse(date_str, dayfirst=False)
            return parsed_dt.date()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date '{date_str}': {str(e)}")
            return None
    
    @staticmethod
    def parse_robust_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string using dateutil with comprehensive error handling"""
        if not date_str:
            return None
        
        try:
            # Use dateutil parser for robust datetime parsing
            return dateutil_parser.parse(date_str, dayfirst=False)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse datetime '{date_str}': {str(e)}")
            return None
    
    @staticmethod
    def parse_numeric_value(value: Any) -> Optional[float]:
        """Parse numeric value from various formats"""
        if value is None:
            return None
        
        try:
            # Remove common non-numeric characters
            value_str = str(value).strip()
            value_str = value_str.replace(",", "").replace("<", "").replace(">", "")
            
            # Extract first number found
            numbers = re.findall(r'\d+\.?\d*', value_str)
            if numbers:
                return float(numbers[0])
            
            return None
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def extract_dosage(cls, event: Dict[str, Any]) -> Optional[str]:
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
    
    @classmethod
    def extract_frequency(cls, event: Dict[str, Any]) -> MedicationFrequency:
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
        for freq_text, freq_enum in cls.FREQUENCY_MAPPING.items():
            if freq_text in search_text:
                return freq_enum
        
        # Default frequency
        return MedicationFrequency.AS_NEEDED
    
    @classmethod
    def extract_severity(cls, event: Dict[str, Any]) -> SymptomSeverity:
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
        for severity_text, severity_enum in cls.SEVERITY_MAPPING.items():
            if severity_text in search_text:
                return severity_enum
        
        # Default severity
        return SymptomSeverity.MODERATE
    
    @classmethod
    def map_health_reading_type(cls, test_name: str) -> HealthReadingType:
        """Map test name to health reading type"""
        test_name_lower = test_name.lower()
        
        for key, reading_type in cls.HEALTH_READING_MAPPING.items():
            if key in test_name_lower:
                return reading_type
        
        # Default to OTHER for unrecognized tests
        return HealthReadingType.OTHER

class AutoPopulationService:
    """
    Service for automatically populating structured tables from extracted medical events
    Fixed for async operations with proper transaction management and bulk duplicate detection
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = MedicalDataExtractor()
    
    async def populate_from_extracted_data(
        self, 
        user_id: str, 
        extracted_data: ExtractedData,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Main method to populate structured tables from extracted medical events
        With proper transaction management and bulk duplicate detection
        
        Returns:
            Dict with counts of created entries and any errors
        """
        # Validate and convert UUIDs upfront
        try:
            user_uuid = uuid.UUID(user_id)
            document_uuid = uuid.UUID(document_id) if document_id else None
        except ValueError as e:
            return {
                "medications_created": 0,
                "symptoms_created": 0,
                "health_readings_created": 0,
                "errors": [f"Invalid UUID format: {str(e)}"],
                "skipped_duplicates": 0
            }
        
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
        
        
        async with self.db.begin():
            try:
                
                existing_records = await self._fetch_existing_records(user_uuid)
                
                
                processing_results = []
                for event in extracted_data.content:
                    try:
                        event_result = await self._process_single_event(
                            user_uuid, event, document_uuid, existing_records
                        )
                        processing_results.append(event_result)
                        
                        
                        if event_result.success and not event_result.was_duplicate:
                            await self._update_existing_records_cache(
                                existing_records, event_result, event
                            )
                        
                    except Exception as e:
                        error_msg = f"Failed to process event {event.get('description', 'unknown')}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        processing_results.append(ProcessingResult(
                            success=False,
                            event_type=event.get("event_type", "unknown"),
                            event_description=event.get("description", "unknown"),
                            error_message=error_msg
                        ))
                
                
                for res in processing_results:
                    if res.success:
                        if res.event_type == "medication":
                            result["medications_created"] += 1
                        elif res.event_type == "symptom":
                            result["symptoms_created"] += 1
                        elif res.event_type in ["labresult", "lab_result", "vitalsign", "vital_sign"]:
                            result["health_readings_created"] += 1
                    elif res.was_duplicate:
                        result["skipped_duplicates"] += 1
                    else:
                        result["errors"].append(res.error_message)
                
                
                logger.info(f"Auto-population completed successfully: {result}")
                
            except Exception as e:
                logger.error(f"Transaction failed during auto-population: {str(e)}", exc_info=True)
                result["errors"].append(f"Transaction failed: {str(e)}")
               
                raise
        
        return result
    
    async def _fetch_existing_records(self, user_uuid: uuid.UUID) -> ExistingRecords:
        """Bulk fetch existing records for efficient duplicate detection"""
        logger.debug(f"Fetching existing records for user {user_uuid}")
        
        
        medications_stmt = select(Medication).where(
            and_(
                Medication.user_id == user_uuid,
                Medication.status == MedicationStatus.ACTIVE
            )
        )
        medications_result = await self.db.execute(medications_stmt)
        medications = {
            med.name.lower(): med 
            for med in medications_result.scalars().all()
        }
        
       
        cutoff_date =  datetime.now(timezone.utc)() - timedelta(days=7)
        symptoms_stmt = select(Symptom).where(
            and_(
                Symptom.user_id == user_uuid,
                Symptom.reported_date >= cutoff_date
            )
        )
        symptoms_result = await self.db.execute(symptoms_stmt)
        symptoms = {
            (sym.symptom.lower(), sym.reported_date.date()): sym
            for sym in symptoms_result.scalars().all()
        }
        
        
        today =  datetime.now(timezone.utc)().date()
        readings_stmt = select(HealthReading).where(
            and_(
                HealthReading.user_id == user_uuid,
                HealthReading.reading_date >= today,
                HealthReading.reading_date < today + timedelta(days=1)
            )
        )
        readings_result = await self.db.execute(readings_stmt)
        health_readings = {
            (reading.reading_type, reading.reading_date.date()): reading
            for reading in readings_result.scalars().all()
        }
        
        logger.debug(f"Fetched {len(medications)} medications, {len(symptoms)} symptoms, {len(health_readings)} health readings")
        
        return ExistingRecords(
            medications=medications,
            symptoms=symptoms,
            health_readings=health_readings
        )
    
    async def _process_single_event(
        self,
        user_uuid: uuid.UUID,
        event: Dict[str, Any],
        document_uuid: Optional[uuid.UUID],
        existing_records: ExistingRecords
    ) -> ProcessingResult:
        """Process a single event with proper error categorization"""
        event_type = event.get("event_type", "").lower()
        event_description = event.get("description", "").strip()
        
        if not event_description:
            return ProcessingResult(
                success=False,
                event_type=event_type,
                event_description="empty",
                error_message="Event has empty description"
            )
        
        try:
            if event_type == "medication":
                return await self._create_medication_from_event(
                    user_uuid, event, document_uuid, existing_records
                )
            elif event_type == "symptom":
                return await self._create_symptom_from_event(
                    user_uuid, event, document_uuid, existing_records
                )
            elif event_type in ["labresult", "lab_result", "vitalsign", "vital_sign"]:
                return await self._create_health_reading_from_event(
                    user_uuid, event, document_uuid, existing_records
                )
            else:
                logger.debug(f"Skipping unsupported event type: {event_type}")
                return ProcessingResult(
                    success=False,
                    event_type=event_type,
                    event_description=event_description,
                    error_message=f"Unsupported event type: {event_type}"
                )
                
        except Exception as e:
            logger.error(f"Error processing {event_type} event: {str(e)}", exc_info=True)
            return ProcessingResult(
                success=False,
                event_type=event_type,
                event_description=event_description,
                error_message=str(e)
            )
    
    async def _update_existing_records_cache(
        self,
        existing_records: ExistingRecords,
        result: ProcessingResult,
        event: Dict[str, Any]
    ):
        """Update the existing records cache when new records are created"""
        if result.event_type == "medication":
            medication_name = event.get("description", "").lower()
            
            existing_records.medications[medication_name] = None  
            
        elif result.event_type == "symptom":
            symptom_name = event.get("description", "").lower()
            event_date = self.extractor.parse_robust_datetime(event.get("date_time"))
            if event_date:
                key = (symptom_name, event_date.date())
                existing_records.symptoms[key] = None  
                
        elif result.event_type in ["labresult", "lab_result", "vitalsign", "vital_sign"]:
            test_name = event.get("description", "").lower()
            reading_type = self.extractor.map_health_reading_type(test_name)
            event_date = self.extractor.parse_robust_datetime(event.get("date_time"))
            if event_date:
                key = (reading_type, event_date.date())
                existing_records.health_readings[key] = None 
    
    async def _create_medication_from_event(
        self, 
        user_uuid: uuid.UUID, 
        event: Dict[str, Any], 
        document_uuid: Optional[uuid.UUID],
        existing_records: ExistingRecords
    ) -> ProcessingResult:
        """Create medication entry from extracted event"""
        medication_name = event.get("description", "").strip()
        
        # Check for duplicates using bulk fetched data
        if medication_name.lower() in existing_records.medications:
            logger.info(f"Skipping duplicate medication: {medication_name}")
            return ProcessingResult(
                success=True,
                event_type="medication",
                event_description=medication_name,
                was_duplicate=True
            )
        
        # Parse dosage and frequency using extractor
        dosage = self.extractor.extract_dosage(event)
        frequency = self.extractor.extract_frequency(event)
        
        # Parse date using robust parser
        start_date = self.extractor.parse_robust_date(event.get("date_time"))
        
        # Create medication
        medication_data = MedicationCreate(
            name=medication_name,
            dosage=dosage,
            frequency=frequency,
            start_date=start_date,
            status=MedicationStatus.ACTIVE,
            notes=f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}",
            related_document_id=document_uuid
        )
        
        # Use async session directly for creation
        db_medication = Medication(**medication_data.model_dump(), user_id=user_uuid)
        self.db.add(db_medication)
        await self.db.flush()  # Get ID without committing
        
        logger.info(f"Created medication: {medication_name} for user {user_uuid}")
        return ProcessingResult(
            success=True,
            event_type="medication",
            event_description=medication_name
        )
    
    async def _create_symptom_from_event(
        self, 
        user_uuid: uuid.UUID, 
        event: Dict[str, Any], 
        document_uuid: Optional[uuid.UUID],
        existing_records: ExistingRecords
    ) -> ProcessingResult:
        """Create symptom entry from extracted event"""
        symptom_name = event.get("description", "").strip()
        
        
        reported_date = self.extractor.parse_robust_datetime(event.get("date_time"))
        event_date = reported_date.date() if reported_date else  datetime.now(timezone.utc)().date()
        
        
        duplicate_key = (symptom_name.lower(), event_date)
        if duplicate_key in existing_records.symptoms:
            logger.info(f"Skipping duplicate symptom: {symptom_name} on {event_date}")
            return ProcessingResult(
                success=True,
                event_type="symptom",
                event_description=symptom_name,
                was_duplicate=True
            )
        
        
        severity = self.extractor.extract_severity(event)
        
        
        location = event.get("body_location")
        notes = f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}"
        if event.get("notes"):
            notes += f" | Additional notes: {event.get('notes')}"
        
       
        symptom_data = SymptomCreate(
            symptom=symptom_name,
            severity=severity,
            reported_date=reported_date or  datetime.now(timezone.utc)(),
            location=location,
            notes=notes
        )
        
        
        db_symptom = Symptom(**symptom_data.model_dump(), user_id=user_uuid)
        self.db.add(db_symptom)
        await self.db.flush()  
        
        logger.info(f"Created symptom: {symptom_name} for user {user_uuid}")
        return ProcessingResult(
            success=True,
            event_type="symptom",
            event_description=symptom_name
        )
    
    async def _create_health_reading_from_event(
        self, 
        user_uuid: uuid.UUID, 
        event: Dict[str, Any], 
        document_uuid: Optional[uuid.UUID],
        existing_records: ExistingRecords
    ) -> ProcessingResult:
        """Create health reading entry from extracted event"""
        test_name = event.get("description", "").strip().lower()
        
      
        reading_type = self.extractor.map_health_reading_type(test_name)
        
       
        value = event.get("value")
        units = event.get("units")
        
        if not value:
            logger.warning(f"Skipping health reading {test_name} with no value")
            return ProcessingResult(
                success=False,
                event_type="health_reading",
                event_description=test_name,
                error_message="No value provided"
            )
        
        
        reading_date = self.extractor.parse_robust_datetime(event.get("date_time"))
        event_date = reading_date.date() if reading_date else  datetime.now(timezone.utc)().date()
        
        
        duplicate_key = (reading_type, event_date)
        if duplicate_key in existing_records.health_readings:
            logger.info(f"Skipping duplicate health reading: {test_name} on {event_date}")
            return ProcessingResult(
                success=True,
                event_type="health_reading",
                event_description=test_name,
                was_duplicate=True
            )
        
        
        systolic_value = None
        diastolic_value = None
        numeric_value = None
        
        if reading_type == HealthReadingType.BLOOD_PRESSURE and "/" in str(value):
            
            try:
                bp_parts = str(value).split("/")
                systolic_value = int(bp_parts[0].strip())
                diastolic_value = int(bp_parts[1].strip())
            except (ValueError, IndexError):
                numeric_value = self.extractor.parse_numeric_value(value)
        else:
            numeric_value = self.extractor.parse_numeric_value(value)
        
        
        health_reading_data = HealthReadingCreate(
            reading_type=reading_type,
            numeric_value=numeric_value,
            systolic_value=systolic_value,
            diastolic_value=diastolic_value,
            unit=units,
            reading_date=reading_date or  datetime.now(timezone.utc)(),
            notes=f"Auto-populated from document. Raw text: {event.get('raw_text_snippet', '')[:200]}",
            source="Document Upload",
            related_document_id=document_uuid
        )
        
       
        db_health_reading = HealthReading(**health_reading_data.model_dump(), user_id=user_uuid)
        self.db.add(db_health_reading)
        await self.db.flush()  
        
        logger.info(f"Created health reading: {test_name} = {value} {units} for user {user_uuid}")
        return ProcessingResult(
            success=True,
            event_type="health_reading",
            event_description=test_name
        )
    
def get_auto_population_service(db: AsyncSession) -> AutoPopulationService:
    """Factory function to get auto-population service"""
    return AutoPopulationService(db) 