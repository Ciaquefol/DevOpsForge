import logging
import threading
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from application.activity.service import ActivityService
from config import settings
from domain.activity.entities import ActivityType
from domain.deployment.entities import Deployment, DeploymentStatus
from infrastructure.docker.service import DockerDeployService
from infrastructure.git.client import GitClient
from infrastructure.persistence.models import DeploymentModel, TaskModel

logger = logging.getLogger(__name__)


class DeploymentService:
    def __init__(self, db: Session):
        self.db = db
        self.activity = ActivityService(db)
        self.git = GitClient()
        self.docker = DockerDeployService()

    def _to_entity(self, row: DeploymentModel) -> Deployment:
        return Deployment(
            id=row.id,
            app_name=row.app_name,
            repo_url=row.repo_url,
            branch=row.branch,
            version=row.version,
            git_sha=row.git_sha,
            image_tag=row.image_tag,
            status=DeploymentStatus(row.status),
            initiated_by=row.initiated_by,
            log_output=row.log_output,
            started_at=row.started_at,
            finished_at=row.finished_at,
            rollback_of_id=row.rollback_of_id,
            task_id=row.task_id,
        )

    def list_deployments(self, limit: int = 50) -> list[Deployment]:
        rows = (
            self.db.query(DeploymentModel)
            .order_by(DeploymentModel.started_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(r) for r in rows]

    def get_deployment(self, deployment_id: int) -> Deployment:
        row = self.db.get(DeploymentModel, deployment_id)
        if not row:
            raise HTTPException(404, "Деплой не найден")
        return self._to_entity(row)

    def get_last_successful(self, app_name: str, exclude_id: int | None = None) -> DeploymentModel | None:
        q = self.db.query(DeploymentModel).filter(
            DeploymentModel.app_name == app_name,
            DeploymentModel.status == DeploymentStatus.SUCCESS.value,
        )
        if exclude_id:
            q = q.filter(DeploymentModel.id != exclude_id)
        return q.order_by(DeploymentModel.finished_at.desc()).first()

    def start_deploy(
        self,
        app_name: str,
        repo_url: str,
        branch: str,
        initiated_by: str,
        rollback_of_id: int | None = None,
        task_id: int | None = None,
    ) -> Deployment:
        resolved_repo = repo_url
        resolved_branch = branch or "main"
        if task_id:
            task = self.db.get(TaskModel, task_id)
            if task:
                if task.repo_url:
                    resolved_repo = task.repo_url
                if task.git_branch:
                    resolved_branch = task.git_branch

        row = DeploymentModel(
            app_name=app_name,
            repo_url=resolved_repo,
            branch=resolved_branch,
            status=DeploymentStatus.PENDING.value,
            initiated_by=initiated_by,
            started_at=datetime.now(),
            rollback_of_id=rollback_of_id,
            task_id=task_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        self.activity.record(
            ActivityType.DEPLOY_STARTED if not rollback_of_id else ActivityType.ROLLBACK_STARTED,
            initiated_by,
            f"{'Откат' if rollback_of_id else 'Деплой'} {app_name} запущен (#{row.id})",
            "deployment",
            row.id,
        )
        thread = threading.Thread(
            target=self._run_deploy_job,
            args=(row.id,),
            daemon=True,
        )
        thread.start()
        return self._to_entity(row)

    def rollback(self, deployment_id: int, initiated_by: str) -> Deployment:
        current = self.db.get(DeploymentModel, deployment_id)
        if not current:
            raise HTTPException(404, "Деплой не найден")
        previous = self.get_last_successful(current.app_name, exclude_id=deployment_id)
        if not previous or not previous.image_tag:
            raise HTTPException(400, "Нет предыдущей успешной версии для отката")

        row = DeploymentModel(
            app_name=current.app_name,
            repo_url=previous.repo_url,
            branch=previous.branch,
            version=previous.version,
            git_sha=previous.git_sha,
            image_tag=previous.image_tag,
            status=DeploymentStatus.PENDING.value,
            initiated_by=initiated_by,
            started_at=datetime.now(),
            rollback_of_id=deployment_id,
            log_output=f"Rollback to image {previous.image_tag}",
        )
        self.db.add(row)
        current.status = DeploymentStatus.ROLLED_BACK.value
        self.db.commit()
        self.db.refresh(row)
        self.activity.record(
            ActivityType.ROLLBACK_STARTED,
            initiated_by,
            f"Откат {current.app_name} к версии {previous.version}",
            "deployment",
            row.id,
        )
        thread = threading.Thread(
            target=self._run_rollback_job,
            args=(row.id,),
            daemon=True,
        )
        thread.start()
        return self._to_entity(row)

    def _run_rollback_job(self, deployment_id: int):
        from infrastructure.persistence.database import SessionLocal

        db = SessionLocal()
        try:
            row = db.get(DeploymentModel, deployment_id)
            if not row or not row.image_tag:
                return
            logs = []
            row.status = DeploymentStatus.DEPLOYING.value
            db.commit()
            docker = DockerDeployService()
            if docker.is_available():
                try:
                    msg = docker.run_container(row.image_tag, row.app_name)
                    logs.append(msg)
                    row.status = DeploymentStatus.SUCCESS.value
                except Exception as exc:
                    logs.append(str(exc))
                    row.status = DeploymentStatus.FAILED.value
            else:
                logs.append("Docker недоступен — откат зафиксирован в истории")
                row.status = DeploymentStatus.SUCCESS.value
            row.log_output = (row.log_output or "") + "\n" + "\n".join(logs)
            row.finished_at = datetime.now()
            db.commit()
            activity = ActivityService(db)
            activity.record(
                ActivityType.ROLLBACK_FINISHED,
                row.initiated_by,
                f"Откат #{row.id}: {row.status}",
                "deployment",
                row.id,
            )
        finally:
            db.close()

    def _run_deploy_job(self, deployment_id: int):
        from infrastructure.persistence.database import SessionLocal

        db = SessionLocal()
        try:
            self._execute_deploy(db, deployment_id)
        finally:
            db.close()

    def _execute_deploy(self, db: Session, deployment_id: int):
        row = db.get(DeploymentModel, deployment_id)
        if not row:
            return
        logs: list[str] = []
        activity = ActivityService(db)
        docker = DockerDeployService()

        def update_status(status: DeploymentStatus, extra_log: str = ""):
            row.status = status.value
            if extra_log:
                logs.append(extra_log)
            row.log_output = "\n".join(logs)
            db.commit()

        try:
            update_status(DeploymentStatus.CLONING, "Клонирование репозитория...")
            workspace = Path(settings.deploy_workspace) / f"{row.app_name}-{deployment_id}"
            sha, version = self.git.clone_or_pull(row.repo_url, row.branch or "main", workspace)
            row.git_sha = sha
            row.version = version
            db.commit()
            logs.append(f"Git SHA: {sha}")

            image_tag = f"devopsforge/{row.app_name}:{version}"
            row.image_tag = image_tag
            db.commit()

            dockerfile = self.git.read_dockerfile(workspace)
            if dockerfile and docker.is_available():
                update_status(DeploymentStatus.BUILDING, "Сборка Docker-образа...")
                build_log = docker.build_image(workspace, image_tag)
                logs.append(build_log)
                update_status(DeploymentStatus.DEPLOYING, "Запуск контейнера...")
                run_log = docker.run_container(
                    image_tag,
                    row.app_name,
                    git_branch=row.branch,
                    task_id=row.task_id,
                )
                logs.append(run_log)
            elif docker.is_available():
                logs.append("Dockerfile не найден — образ не собран, деплой записан")
            else:
                logs.append("Docker недоступен — симуляция успешного деплоя")

            row.status = DeploymentStatus.SUCCESS.value
            row.finished_at = datetime.now()
            row.log_output = "\n".join(logs)
            db.commit()
            activity.record(
                ActivityType.DEPLOY_FINISHED,
                row.initiated_by,
                f"Деплой #{row.id} успешен (v{row.version})",
                "deployment",
                row.id,
            )
        except Exception as exc:
            logger.exception("Deploy failed")
            row.status = DeploymentStatus.FAILED.value
            row.finished_at = datetime.now()
            logs.append(f"ERROR: {exc}")
            row.log_output = "\n".join(logs)
            db.commit()
            activity.record(
                ActivityType.DEPLOY_FAILED,
                row.initiated_by,
                f"Деплой #{row.id} провален: {exc}",
                "deployment",
                row.id,
            )
