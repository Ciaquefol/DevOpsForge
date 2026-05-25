from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task:
    id: Optional[int]
    title: str
    description: Optional[str]
    status: TaskStatus
    assigned_to: Optional[str]
    git_branch: Optional[str]
    repo_url: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskHistoryEntry:
    id: Optional[int]
    task_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: str
    changed_at: datetime
