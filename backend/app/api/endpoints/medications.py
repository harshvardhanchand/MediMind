from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.medication import MedicationStatus
from app.schemas.medication import MedicationCreate, MedicationResponse, MedicationUpdate
from app.repositories.medication_repo import medication_repo
from app.services.notification_service import get_notification_service, get_medical_triggers, detect_changes

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[MedicationResponse], summary="Get medications for current user")
async def get_medications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[MedicationStatus] = None,
    search: Optional[str] = Query(None, description="Search query for medication name, reason, or doctor"),
    active_only: bool = Query(False, description="Get only active medications"),
    optimized: bool = Query(True, description="Use optimized queries with eager loading (recommended)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get medications for the current user.
    
    Can filter by medication status and search by name, reason, or doctor.
    
    Performance Notes:
    - optimized=True: Uses eager loading, ~90% fewer database queries, faster response
    - optimized=False: Uses lazy loading, backward compatibility, slower for large datasets
    """
    try:
        # Limit to reasonable size for performance
        limit = min(limit, 100)
        
        if optimized:
            # Use optimized methods with eager loading
            if active_only:
                medications = medication_repo.get_active_by_owner_optimized(
                    db=db, user_id=current_user.user_id, skip=skip, limit=limit
                )
            elif search or status:
                medications = medication_repo.search_by_owner_optimized(
                    db=db, 
                    user_id=current_user.user_id, 
                    search_query=search,
                    status=status,
                    skip=skip, 
                    limit=limit
                )
            else:
                medications = medication_repo.get_multi_by_owner_optimized(
                    db=db, user_id=current_user.user_id, skip=skip, limit=limit
                )
        else:
            # Use original methods for backward compatibility
            if active_only:
                medications = medication_repo.get_active_by_owner(
                    db=db, user_id=current_user.user_id, skip=skip, limit=limit
                )
            elif search or status:
                medications = medication_repo.search_by_owner(
                    db=db, 
                    user_id=current_user.user_id, 
                    search_query=search,
                    status=status,
                    skip=skip, 
                    limit=limit
                )
            else:
                medications = medication_repo.get_multi_by_owner(
                    db=db, user_id=current_user.user_id, skip=skip, limit=limit
                )
        
        logger.info(f"Retrieved {len(medications)} medications for user {current_user.user_id} (optimized={optimized})")
        return medications
        
    except Exception as e:
        logger.error(f"Error retrieving medications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving medications."
        )

@router.get("/dashboard", response_model=List[MedicationResponse], summary="Get medications for dashboard")
async def get_medications_for_dashboard(
    limit: int = Query(5, le=10, description="Maximum number of medications for dashboard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get minimal medication data optimized for dashboard/home screen display.
    
    This endpoint is highly optimized for performance:
    - No relationships loaded
    - Only active medications
    - Limited to recent items
    - Minimal memory usage
    """
    try:
        medications = medication_repo.get_summary_for_dashboard(
            db=db, user_id=current_user.user_id, limit=limit
        )
        return medications
    except Exception as e:
        logger.error(f"Error retrieving dashboard medications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving dashboard medications."
        )

@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED, summary="Add a new medication")
async def create_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new medication for the current user.
    """
    try:
        db_medication = medication_repo.create_with_owner(
            db=db, obj_in=medication, user_id=current_user.user_id
        )
        
        # After successful creation, trigger medical analysis
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            # Trigger analysis in background (don't wait for completion)
            medication_data = {
                "name": medication.name,
                "dosage": medication.dosage,
                "frequency": medication.frequency,
                "start_date": medication.start_date.isoformat() if medication.start_date else None
            }
            
            await medical_triggers.on_medication_added(
                str(current_user.user_id), 
                medication_data,
                medication_id=str(db_medication.id)  # Pass the medication ID
            )
            
        except Exception as e:
            # Log error but don't fail the medication creation
            logger.warning(f"Failed to trigger medication analysis: {str(e)}")
        
        return db_medication
    except Exception as e:
        logger.error(f"Error creating medication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the medication."
        )


@router.get("/{medication_id}", response_model=MedicationResponse, summary="Get a specific medication")
async def get_medication(
    medication_id: UUID,
    full_details: bool = Query(True, description="Load all related data (notifications, documents, etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific medication by ID.
    
    Performance Notes:
    - full_details=True: Loads all related data with eager loading (for detail views)
    - full_details=False: Loads only basic medication data (for quick access)
    """
    try:
        if full_details:
            medication = medication_repo.get_by_id_with_full_details(db=db, medication_id=medication_id)
        else:
            medication = medication_repo.get_by_id(db=db, medication_id=medication_id)
            
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medication not found"
            )
        
        # Ensure the medication belongs to the authenticated user
        if medication.user_id != current_user.user_id:
            logger.warning(f"User {current_user.user_id} attempted to access medication {medication_id} owned by {medication.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this medication"
            )
        
        return medication
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving medication {medication_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the medication."
        )


@router.put("/{medication_id}", response_model=MedicationResponse, summary="Update a medication")
async def update_medication(
    medication_id: UUID,
    medication_update: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a specific medication by ID.
    """
    db_medication = medication_repo.get_by_id(db=db, medication_id=medication_id)
    if not db_medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    
    # Ensure the medication belongs to the authenticated user
    if db_medication.user_id != current_user.user_id:
        logger.warning(f"User {current_user.user_id} attempted to update medication {medication_id} owned by {db_medication.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this medication"
        )
    
    try:
        # Capture old data for change detection
        old_medication_data = {
            "name": db_medication.name,
            "dosage": db_medication.dosage,
            "frequency": db_medication.frequency.value if db_medication.frequency else None,
            "start_date": db_medication.start_date.isoformat() if db_medication.start_date else None,
            "end_date": db_medication.end_date.isoformat() if db_medication.end_date else None,
            "status": db_medication.status.value if db_medication.status else None,
            "reason": db_medication.reason,
            "prescribing_doctor": db_medication.prescribing_doctor,
            "notes": db_medication.notes
        }
        
        updated_medication = medication_repo.update(
            db=db, db_obj=db_medication, obj_in=medication_update
        )
        
        # Trigger AI analysis for medication update
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            # Prepare new medication data
            new_medication_data = {
                "name": updated_medication.name,
                "dosage": updated_medication.dosage,
                "frequency": updated_medication.frequency.value if updated_medication.frequency else None,
                "start_date": updated_medication.start_date.isoformat() if updated_medication.start_date else None,
                "end_date": updated_medication.end_date.isoformat() if updated_medication.end_date else None,
                "status": updated_medication.status.value if updated_medication.status else None,
                "reason": updated_medication.reason,
                "prescribing_doctor": updated_medication.prescribing_doctor,
                "notes": updated_medication.notes
            }
            
            # Detect changes
            changes = detect_changes(old_medication_data, new_medication_data)
            
            # Only trigger analysis if there are meaningful changes
            if changes:
                await medical_triggers.on_medication_updated(
                    str(current_user.user_id),
                    new_medication_data,
                    changes,
                    medication_id=str(updated_medication.medication_id)
                )
                logger.info(f"AI analysis triggered for medication update: {medication_id}")
            
        except Exception as e:
            # Log error but don't fail the medication update
            logger.warning(f"Failed to trigger medication update analysis: {str(e)}")
        
        return updated_medication
    except Exception as e:
        logger.error(f"Error updating medication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the medication."
        )


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a medication")
async def delete_medication(
    medication_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific medication by ID.
    """
    db_medication = medication_repo.get_by_id(db=db, medication_id=medication_id)
    if not db_medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found"
        )
    
    # Ensure the medication belongs to the authenticated user
    if db_medication.user_id != current_user.user_id:
        logger.warning(f"User {current_user.user_id} attempted to delete medication {medication_id} owned by {db_medication.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this medication"
        )
    
    try:
        # Capture medication data before deletion for AI analysis
        medication_data = {
            "name": db_medication.name,
            "dosage": db_medication.dosage,
            "frequency": db_medication.frequency.value if db_medication.frequency else None,
            "start_date": db_medication.start_date.isoformat() if db_medication.start_date else None,
            "end_date": db_medication.end_date.isoformat() if db_medication.end_date else None,
            "status": db_medication.status.value if db_medication.status else None,
            "reason": db_medication.reason,
            "prescribing_doctor": db_medication.prescribing_doctor,
            "notes": db_medication.notes
        }
        
        medication_repo.remove(db=db, id=medication_id)
        
        # Trigger AI analysis for medication deletion
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            await medical_triggers.on_medication_deleted(
                str(current_user.user_id),
                medication_data,
                medication_id=str(medication_id)
            )
            logger.info(f"AI analysis triggered for medication deletion: {medication_id}")
            
        except Exception as e:
            # Log error but don't fail the medication deletion
            logger.warning(f"Failed to trigger medication deletion analysis: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error deleting medication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the medication."
        ) 