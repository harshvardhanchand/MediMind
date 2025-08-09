from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.health_reading import HealthReadingType, HealthReading
from app.models.user import User
from app.schemas.health_reading import (
    HealthReadingCreate,
    HealthReadingResponse,
    HealthReadingUpdate,
)
from app.repositories.health_reading_repo import HealthReadingRepository
from app.services.notification_service import (
    get_notification_service,
    get_medical_triggers,
    detect_changes,
)

router = APIRouter()
logger = logging.getLogger(__name__)


health_reading_repo = HealthReadingRepository(HealthReading)


@router.post(
    "/", response_model=HealthReadingResponse, status_code=status.HTTP_201_CREATED
)
async def create_health_reading(
    health_reading_in: HealthReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new health reading for the current user."""
    try:
        health_reading = health_reading_repo.create_with_owner(
            db=db, obj_in=health_reading_in, user_id=current_user.user_id
        )

        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)

            reading_data = {
                "type": health_reading.type.value if health_reading.type else None,
                "value": health_reading.value,
                "unit": health_reading.unit,
                "recorded_date": (
                    health_reading.recorded_date.isoformat()
                    if health_reading.recorded_date
                    else None
                ),
                "notes": health_reading.notes,
            }

            await medical_triggers.on_health_reading_added(
                str(current_user.user_id),
                reading_data,
                health_reading_id=str(health_reading.health_reading_id),
            )
            logger.info(
                f"AI analysis triggered for new health reading: {health_reading.health_reading_id}"
            )

        except Exception as e:

            logger.warning(f"Failed to trigger health reading analysis: {str(e)}")

        return health_reading
    except Exception as e:
        logger.error(f"Error creating health reading: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the health reading.",
        )


@router.get("/", response_model=List[HealthReadingResponse])
async def get_health_readings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    reading_type: Optional[HealthReadingType] = Query(
        None, description="Filter by reading type"
    ),
    start_date: Optional[str] = Query(
        None, description="Start date for filtering (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(
        None, description="End date for filtering (YYYY-MM-DD)"
    ),
    search: Optional[str] = Query(
        None, description="Search query for notes or text value"
    ),
):
    """Retrieve health readings for the current user, with optional filtering and search."""
    try:
        if search:
            readings = health_reading_repo.search_by_owner(
                db=db,
                user_id=current_user.user_id,
                search_query=search,
                skip=skip,
                limit=limit,
            )
        else:
            readings = health_reading_repo.get_multi_by_owner(
                db=db,
                user_id=current_user.user_id,
                skip=skip,
                limit=limit,
                reading_type=reading_type,
                start_date=start_date,
                end_date=end_date,
            )
        return readings
    except Exception as e:
        logger.error(f"Error retrieving health readings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving health readings.",
        )


@router.get("/{health_reading_id}", response_model=HealthReadingResponse)
async def get_health_reading(
    health_reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific health reading by its ID."""
    reading = health_reading_repo.get_by_id(db=db, health_reading_id=health_reading_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Health reading not found"
        )
    if reading.user_id != current_user.user_id:
        logger.warning(
            f"User {current_user.user_id} attempted to access health reading {health_reading_id} owned by {reading.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this health reading",
        )
    return reading


@router.put("/{health_reading_id}", response_model=HealthReadingResponse)
async def update_health_reading(
    health_reading_id: UUID,
    health_reading_in: HealthReadingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific health reading by its ID."""
    db_reading = health_reading_repo.get_by_id(
        db=db, health_reading_id=health_reading_id
    )
    if not db_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Health reading not found"
        )
    if db_reading.user_id != current_user.user_id:
        logger.warning(
            f"User {current_user.user_id} attempted to update health reading {health_reading_id} owned by {db_reading.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this health reading",
        )

    try:

        old_reading_data = {
            "type": db_reading.type.value if db_reading.type else None,
            "value": db_reading.value,
            "unit": db_reading.unit,
            "recorded_date": (
                db_reading.recorded_date.isoformat()
                if db_reading.recorded_date
                else None
            ),
            "notes": db_reading.notes,
        }

        updated_reading = health_reading_repo.update(
            db=db, db_obj=db_reading, obj_in=health_reading_in
        )

        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)

            new_reading_data = {
                "type": updated_reading.type.value if updated_reading.type else None,
                "value": updated_reading.value,
                "unit": updated_reading.unit,
                "recorded_date": (
                    updated_reading.recorded_date.isoformat()
                    if updated_reading.recorded_date
                    else None
                ),
                "notes": updated_reading.notes,
            }

            changes = detect_changes(old_reading_data, new_reading_data)

            if changes:
                await medical_triggers.on_health_reading_updated(
                    str(current_user.user_id),
                    new_reading_data,
                    changes,
                    health_reading_id=str(updated_reading.health_reading_id),
                )
                logger.info(
                    f"AI analysis triggered for health reading update: {health_reading_id}"
                )

        except Exception as e:

            logger.warning(
                f"Failed to trigger health reading update analysis: {str(e)}"
            )

        return updated_reading
    except Exception as e:
        logger.error(
            f"Error updating health reading {health_reading_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the health reading.",
        )


@router.delete("/{health_reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_reading(
    health_reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific health reading by its ID."""
    db_reading = health_reading_repo.get_by_id(
        db=db, health_reading_id=health_reading_id
    )
    if not db_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Health reading not found"
        )
    if db_reading.user_id != current_user.user_id:
        logger.warning(
            f"User {current_user.user_id} attempted to delete health reading {health_reading_id} owned by {db_reading.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this health reading",
        )

    try:

        reading_data = {
            "type": db_reading.type.value if db_reading.type else None,
            "value": db_reading.value,
            "unit": db_reading.unit,
            "recorded_date": (
                db_reading.recorded_date.isoformat()
                if db_reading.recorded_date
                else None
            ),
            "notes": db_reading.notes,
        }

        health_reading_repo.remove(db=db, id=health_reading_id)

        try:
            notification_service = get_notification_service(db)
            medical_triggers = get_medical_triggers(notification_service)

            await medical_triggers.on_health_reading_deleted(
                str(current_user.user_id),
                reading_data,
                health_reading_id=str(health_reading_id),
            )
            logger.info(
                f"AI analysis triggered for health reading deletion: {health_reading_id}"
            )

        except Exception as e:

            logger.warning(
                f"Failed to trigger health reading deletion analysis: {str(e)}"
            )

    except Exception as e:
        logger.error(
            f"Error deleting health reading {health_reading_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the health reading.",
        )
