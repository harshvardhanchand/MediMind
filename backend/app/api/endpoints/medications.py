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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get medications for the current user.
    
    Can filter by medication status and search by name, reason, or doctor.
    """
    try:
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
        return medications
    except Exception as e:
        logger.error(f"Error retrieving medications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving medications."
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific medication by ID.
    """
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
        updated_medication = medication_repo.update(
            db=db, db_obj=db_medication, obj_in=medication_update
        )
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
        medication_repo.remove(db=db, id=medication_id)
    except Exception as e:
        logger.error(f"Error deleting medication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the medication."
        ) 