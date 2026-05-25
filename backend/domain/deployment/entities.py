from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    BUILDING = "building"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Deployment:
    id: Optional[int]
    app_name: str
    repo_url: str
    branch: str
    version: Optional[str]
    git_sha: Optional[str]
    image_tag: Optional[str]
    status: DeploymentStatus
    initiated_by: str
    log_output: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    rollback_of_id: Optional[int] = None
    task_id: Optional[int] = None
