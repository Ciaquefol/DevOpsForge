from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from application.tasks.service import TaskService
from config import settings
from infrastructure.persistence.database import get_db
from presentation.schemas import GitBranchesSchema

router = APIRouter(prefix="/git", tags=["git"])


@router.get("/branches", response_model=GitBranchesSchema)
def list_branches(
    repo_url: str | None = Query(None, description="URL Git-репозитория"),
    db: Session = Depends(get_db),
):
    url = repo_url or settings.default_repo_url
    service = TaskService(db)
    return GitBranchesSchema(repo_url=url, branches=service.list_branches(url))
