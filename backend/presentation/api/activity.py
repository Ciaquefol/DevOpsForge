from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.activity.service import ActivityService
from infrastructure.persistence.database import get_db
from presentation.schemas import ActivityEventSchema

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityEventSchema])
def list_activity(limit: int = 50, db: Session = Depends(get_db)):
    service = ActivityService(db)
    return [
        ActivityEventSchema(
            id=e.id,
            event_type=e.event_type.value,
            actor=e.actor,
            message=e.message,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            created_at=e.created_at,
        )
        for e in service.list_recent(limit)
    ]
