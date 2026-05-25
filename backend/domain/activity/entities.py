from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ActivityType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_MOVED = "task_moved"
    TASK_DELETED = "task_deleted"
    DEPLOY_STARTED = "deploy_started"
    DEPLOY_FINISHED = "deploy_finished"
    DEPLOY_FAILED = "deploy_failed"
    ROLLBACK_STARTED = "rollback_started"
    ROLLBACK_FINISHED = "rollback_finished"
    METRICS_ALERT = "metrics_alert"


@dataclass
class ActivityEvent:
    id: Optional[int]
    event_type: ActivityType
    actor: str
    message: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    created_at: datetime
