from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.deployment.service import DeploymentService
from infrastructure.persistence.database import get_db
from presentation.schemas import DeploymentCreateSchema, DeploymentSchema

router = APIRouter(prefix="/deployments", tags=["deployments"])


def _to_schema(d) -> DeploymentSchema:
    status = d.status.value if hasattr(d.status, "value") else d.status
    return DeploymentSchema(
        id=d.id,
        app_name=d.app_name,
        repo_url=d.repo_url,
        branch=d.branch,
        version=d.version,
        git_sha=d.git_sha,
        image_tag=d.image_tag,
        status=status,
        initiated_by=d.initiated_by,
        log_output=d.log_output,
        started_at=d.started_at,
        finished_at=d.finished_at,
        rollback_of_id=d.rollback_of_id,
        task_id=d.task_id,
    )


@router.get("", response_model=list[DeploymentSchema])
def list_deployments(limit: int = 50, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    return [_to_schema(d) for d in service.list_deployments(limit)]


@router.get("/{deployment_id}", response_model=DeploymentSchema)
def get_deployment(deployment_id: int, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    return _to_schema(service.get_deployment(deployment_id))


@router.post("", response_model=DeploymentSchema)
def start_deployment(payload: DeploymentCreateSchema, db: Session = Depends(get_db)):
    service = DeploymentService(db)
    deployment = service.start_deploy(
        payload.app_name,
        payload.repo_url,
        payload.branch,
        payload.initiated_by,
        task_id=payload.task_id,
    )
    return _to_schema(deployment)


@router.post("/{deployment_id}/rollback", response_model=DeploymentSchema)
def rollback_deployment(
    deployment_id: int,
    initiated_by: str = "devops",
    db: Session = Depends(get_db),
):
    service = DeploymentService(db)
    return _to_schema(service.rollback(deployment_id, initiated_by))
