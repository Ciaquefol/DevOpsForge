import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class TaskSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    git_branch: Optional[str] = None
    repo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    assigned_to: Optional[str] = None
    repo_url: Optional[str] = None
    git_branch: Optional[str] = None
    create_git_branch: bool = False
    actor: str = "system"


class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    git_branch: Optional[str] = None
    repo_url: Optional[str] = None
    actor: str = "system"


class TaskLinkBranchSchema(BaseModel):
    git_branch: Optional[str] = None
    repo_url: Optional[str] = None
    create_git_branch: bool = False
    actor: str = "system"


class TaskMoveSchema(BaseModel):
    status: str
    actor: str = "system"


class TaskHistorySchema(BaseModel):
    id: int
    task_id: int
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: str
    changed_at: datetime


class GitBranchesSchema(BaseModel):
    repo_url: str
    branches: list[str]


class BootstrapStatusSchema(BaseModel):
    database_seeded: int
    container_workspace: dict


class DeploymentSchema(BaseModel):
    id: int
    app_name: str
    repo_url: str
    branch: str
    version: Optional[str] = None
    git_sha: Optional[str] = None
    image_tag: Optional[str] = None
    status: str
    initiated_by: str
    log_output: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    rollback_of_id: Optional[int] = None
    task_id: Optional[int] = None


class DeploymentCreateSchema(BaseModel):
    app_name: str
    repo_url: str
    branch: str = "main"
    initiated_by: str = "devops"
    task_id: Optional[int] = None


class MetricSampleSchema(BaseModel):
    id: int
    host: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    process_count: int
    top_processes: list[dict[str, Any]] = []
    recorded_at: datetime


def parse_top_processes(raw: str | None) -> list[dict[str, Any]]:
    """Безопасно превращает JSON-строку из БД в список словарей."""
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


class ActivityEventSchema(BaseModel):
    id: int
    event_type: str
    actor: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
