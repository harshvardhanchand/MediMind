"""
Symptoms API Endpoints
Provides REST API for symptom tracking and management
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Path
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.symptom import SymptomSeverity
from app.schemas.symptom import (
    SymptomCreate, SymptomUpdate, SymptomResponse, SymptomListResponse,
    SymptomStatsResponse, SymptomSearchRequest, SymptomAnalysisRequest,
    SymptomCorrelationResponse, SymptomBulkCreateRequest, SymptomBulkCreateResponse
)
from app.repositories.symptom_repo import symptom_repo
from app.services.notification_service import get_notification_service, get_medical_triggers, detect_changes

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=SymptomListResponse, summary="Get symptoms for current user")
async def get_symptoms(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    severity: Optional[SymptomSeverity] = Query(None, description="Filter by severity level"),
    start_date: Optional[datetime] = Query(None, description="Filter symptoms from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter symptoms until this date"),
    search: Optional[str] = Query(None, description="Search in symptom name or notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get symptoms for the current user with optional filtering and search.
    
    Supports filtering by:
    - Severity level
    - Date range
    - Search in symptom name or notes
    """
    try:
        if search:
            # Use search functionality
            symptoms = symptom_repo.search_symptoms(
                db=db, 
                user_id=current_user.user_id, 
                search_query=search,
                skip=skip, 
                limit=limit
            )
            # Get total count for search results (simplified)
            total = len(symptom_repo.search_symptoms(
                db=db, 
                user_id=current_user.user_id, 
                search_query=search,
                skip=0, 
                limit=1000  # Get a large number to count
            ))
        else:
            # Use filtered query
            symptoms = symptom_repo.get_by_user(
                db=db,
                user_id=current_user.user_id,
                skip=skip,
                limit=limit,
                severity=severity,
                start_date=start_date,
                end_date=end_date
            )
            # Get total count (simplified - in production, you'd want a separate count query)
            total = len(symptom_repo.get_by_user(
                db=db,
                user_id=current_user.user_id,
                skip=0,
                limit=1000,  # Get a large number to count
                severity=severity,
                start_date=start_date,
                end_date=end_date
            ))
        
        return SymptomListResponse(
            symptoms=symptoms,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving symptoms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving symptoms."
        )


@router.post("/", response_model=SymptomResponse, status_code=status.HTTP_201_CREATED, summary="Create a new symptom")
async def create_symptom(
    symptom: SymptomCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new symptom for the current user.
    
    Automatically triggers medical analysis to check for correlations
    with medications and patterns.
    """
    try:
        # Set reported_date to now if not provided
        if not symptom.reported_date:
            symptom.reported_date = datetime.utcnow()
        
        # Create the symptom
        db_symptom = symptom_repo.create_with_user(
            db=db, 
            obj_in=symptom, 
            user_id=current_user.user_id
        )
        
        # Trigger medical analysis in background
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            # Prepare symptom data for analysis
            symptom_data = {
                "symptom": symptom.symptom,
                "severity": symptom.severity.value,
                "duration": symptom.duration,
                "location": symptom.location,
                "notes": symptom.notes,
                "reported_date": symptom.reported_date.isoformat()
            }
            
            # Trigger analysis in background
            background_tasks.add_task(
                medical_triggers.on_symptom_reported,
                str(current_user.user_id),
                symptom_data
            )
            
            logger.info(f"Triggered medical analysis for symptom: {symptom.symptom}")
            
        except Exception as e:
            # Log error but don't fail the symptom creation
            logger.warning(f"Failed to trigger symptom analysis: {str(e)}")
        
        return db_symptom
        
    except Exception as e:
        logger.error(f"Error creating symptom: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the symptom."
        )


@router.get("/{symptom_id}", response_model=SymptomResponse, summary="Get a specific symptom")
async def get_symptom(
    symptom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific symptom by ID.
    """
    symptom = symptom_repo.get_by_id_and_user(
        db=db, 
        symptom_id=symptom_id, 
        user_id=current_user.user_id
    )
    
    if not symptom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom not found"
        )
    
    return symptom


@router.put("/{symptom_id}", response_model=SymptomResponse, summary="Update a symptom")
async def update_symptom(
    symptom_id: UUID,
    symptom_update: SymptomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a specific symptom by ID.
    """
    try:
        # Get the existing symptom first for change detection
        existing_symptom = symptom_repo.get_by_user(
            db=db,
            symptom_id=symptom_id,
            user_id=current_user.user_id
        )
        
        if not existing_symptom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom not found"
            )
        
        # Capture old data for change detection
        old_symptom_data = {
            "symptom": existing_symptom.symptom,
            "severity": existing_symptom.severity.value if existing_symptom.severity else None,
            "duration": existing_symptom.duration,
            "location": existing_symptom.location,
            "notes": existing_symptom.notes,
            "reported_date": existing_symptom.reported_date.isoformat() if existing_symptom.reported_date else None
        }
        
        updated_symptom = symptom_repo.update_by_user(
            db=db,
            symptom_id=symptom_id,
            user_id=current_user.user_id,
            obj_in=symptom_update
        )
        
        if not updated_symptom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom not found"
            )
        
        # Trigger AI analysis for symptom update
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            # Prepare new symptom data
            new_symptom_data = {
                "symptom": updated_symptom.symptom,
                "severity": updated_symptom.severity.value if updated_symptom.severity else None,
                "duration": updated_symptom.duration,
                "location": updated_symptom.location,
                "notes": updated_symptom.notes,
                "reported_date": updated_symptom.reported_date.isoformat() if updated_symptom.reported_date else None
            }
            
            # Detect changes
            changes = detect_changes(old_symptom_data, new_symptom_data)
            
            # Only trigger analysis if there are meaningful changes
            if changes:
                await medical_triggers.on_symptom_updated(
                    str(current_user.user_id),
                    new_symptom_data,
                    changes,
                    symptom_id=str(updated_symptom.symptom_id)
                )
                logger.info(f"AI analysis triggered for symptom update: {symptom_id}")
            
        except Exception as e:
            # Log error but don't fail the symptom update
            logger.warning(f"Failed to trigger symptom update analysis: {str(e)}")
        
        return updated_symptom
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating symptom: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the symptom."
        )


@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a symptom")
async def delete_symptom(
    symptom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific symptom by ID.
    """
    try:
        # Get the symptom data before deletion for AI analysis
        existing_symptom = symptom_repo.get_by_user(
            db=db,
            symptom_id=symptom_id,
            user_id=current_user.user_id
        )
        
        if not existing_symptom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom not found"
            )
        
        # Capture symptom data before deletion
        symptom_data = {
            "symptom": existing_symptom.symptom,
            "severity": existing_symptom.severity.value if existing_symptom.severity else None,
            "duration": existing_symptom.duration,
            "location": existing_symptom.location,
            "notes": existing_symptom.notes,
            "reported_date": existing_symptom.reported_date.isoformat() if existing_symptom.reported_date else None
        }
        
        success = symptom_repo.delete_by_user(
            db=db,
            symptom_id=symptom_id,
            user_id=current_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom not found"
            )
        
        # Trigger AI analysis for symptom deletion
        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)
            
            await medical_triggers.on_symptom_deleted(
                str(current_user.user_id),
                symptom_data,
                symptom_id=str(symptom_id)
            )
            logger.info(f"AI analysis triggered for symptom deletion: {symptom_id}")
            
        except Exception as e:
            # Log error but don't fail the symptom deletion
            logger.warning(f"Failed to trigger symptom deletion analysis: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting symptom: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the symptom."
        )


@router.get("/stats/overview", response_model=SymptomStatsResponse, summary="Get symptom statistics")
async def get_symptom_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get symptom statistics for the current user.
    """
    try:
        stats = symptom_repo.get_symptom_stats(db=db, user_id=current_user.user_id)
        return SymptomStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error retrieving symptom stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving symptom statistics."
        )


@router.get("/recent/{days}", response_model=List[SymptomResponse], summary="Get recent symptoms")
async def get_recent_symptoms(
    days: int = Path(..., ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of symptoms to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent symptoms for the current user within the specified number of days.
    """
    try:
        symptoms = symptom_repo.get_recent_by_user(
            db=db,
            user_id=current_user.user_id,
            days=days,
            limit=limit
        )
        return symptoms
        
    except Exception as e:
        logger.error(f"Error retrieving recent symptoms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving recent symptoms."
        )


@router.get("/by-severity/{severity}", response_model=List[SymptomResponse], summary="Get symptoms by severity")
async def get_symptoms_by_severity(
    severity: SymptomSeverity,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of symptoms to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get symptoms filtered by severity level.
    """
    try:
        symptoms = symptom_repo.get_by_severity(
            db=db,
            user_id=current_user.user_id,
            severity=severity,
            limit=limit
        )
        return symptoms
        
    except Exception as e:
        logger.error(f"Error retrieving symptoms by severity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving symptoms by severity."
        )


@router.get("/patterns/{symptom_name}", response_model=List[SymptomResponse], summary="Get symptom patterns")
async def get_symptom_patterns(
    symptom_name: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of symptoms to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical patterns for a specific symptom name.
    """
    try:
        symptoms = symptom_repo.get_by_symptom_name(
            db=db,
            user_id=current_user.user_id,
            symptom_name=symptom_name,
            limit=limit
        )
        return symptoms
        
    except Exception as e:
        logger.error(f"Error retrieving symptom patterns: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving symptom patterns."
        )


@router.post("/bulk", response_model=SymptomBulkCreateResponse, summary="Create multiple symptoms")
async def create_symptoms_bulk(
    request: SymptomBulkCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create multiple symptoms at once.
    """
    created_symptoms = []
    failed_symptoms = []
    
    try:
        for i, symptom_data in enumerate(request.symptoms):
            try:
                # Set reported_date to now if not provided
                if not symptom_data.reported_date:
                    symptom_data.reported_date = datetime.utcnow()
                
                # Create the symptom
                db_symptom = symptom_repo.create_with_user(
                    db=db,
                    obj_in=symptom_data,
                    user_id=current_user.user_id
                )
                created_symptoms.append(db_symptom)
                
            except Exception as e:
                failed_symptoms.append({
                    "index": i,
                    "symptom_data": symptom_data.dict(),
                    "error": str(e)
                })
                logger.error(f"Failed to create symptom at index {i}: {str(e)}")
        
        # Trigger analysis for all created symptoms in background
        if created_symptoms:
            try:
                notification_service = get_notification_service(db)
                medical_triggers = get_medical_triggers(notification_service)
                
                for symptom in created_symptoms:
                    symptom_data = {
                        "symptom": symptom.symptom,
                        "severity": symptom.severity.value,
                        "duration": symptom.duration,
                        "location": symptom.location,
                        "notes": symptom.notes,
                        "reported_date": symptom.reported_date.isoformat()
                    }
                    
                    background_tasks.add_task(
                        medical_triggers.on_symptom_reported,
                        str(current_user.user_id),
                        symptom_data
                    )
                
            except Exception as e:
                logger.warning(f"Failed to trigger bulk symptom analysis: {str(e)}")
        
        return SymptomBulkCreateResponse(
            created_symptoms=created_symptoms,
            failed_symptoms=failed_symptoms,
            total_created=len(created_symptoms),
            total_failed=len(failed_symptoms)
        )
        
    except Exception as e:
        logger.error(f"Error in bulk symptom creation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during bulk symptom creation."
        ) 