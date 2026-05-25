from datetime import datetime

from sqlalchemy.orm import Session

from domain.activity.entities import ActivityEvent, ActivityType
from infrastructure.activity.broadcaster import broadcaster
from infrastructure.persistence.models import ActivityEventModel


class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        event_type: ActivityType,
        actor: str,
        message: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> ActivityEvent:
        row = ActivityEventModel(
            event_type=event_type.value,
            actor=actor,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            created_at=datetime.now(),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        payload = {
            "id": row.id,
            "event_type": row.event_type,
            "actor": row.actor,
            "message": row.message,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "created_at": row.created_at.isoformat(),
        }
        broadcaster.publish_sync(payload)
        return ActivityEvent(
            id=row.id,
            event_type=ActivityType(row.event_type),
            actor=row.actor,
            message=row.message,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            created_at=row.created_at,
        )

    def list_recent(self, limit: int = 50) -> list[ActivityEvent]:
        rows = (
            self.db.query(ActivityEventModel)
            .order_by(ActivityEventModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            ActivityEvent(
                id=r.id,
                event_type=ActivityType(r.event_type),
                actor=r.actor,
                message=r.message,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                created_at=r.created_at,
            )
            for r in rows
        ]
