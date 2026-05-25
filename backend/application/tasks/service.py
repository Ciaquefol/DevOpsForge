from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from application.activity.service import ActivityService
from config import settings
from domain.activity.entities import ActivityType
from domain.tasks.entities import Task, TaskHistoryEntry, TaskStatus
from infrastructure.git.client import GitClient
from infrastructure.persistence.models import TaskHistoryModel, TaskModel

ALLOWED_STATUSES = {s.value for s in TaskStatus}


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.activity = ActivityService(db)
        self.git = GitClient()

    def _to_entity(self, row: TaskModel) -> Task:
        return Task(
            id=row.id,
            title=row.title,
            description=row.description,
            status=TaskStatus(row.status),
            assigned_to=row.assigned_to,
            git_branch=row.git_branch,
            repo_url=row.repo_url,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _log_change(
        self,
        task_id: int,
        field_name: str,
        old_value: str | None,
        new_value: str | None,
        changed_by: str,
    ):
        self.db.add(
            TaskHistoryModel(
                task_id=task_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                changed_at=datetime.now(),
            )
        )

    def list_tasks(self) -> list[Task]:
        rows = self.db.query(TaskModel).order_by(TaskModel.id).all()
        return [self._to_entity(r) for r in rows]

    def list_branches(self, repo_url: str | None) -> list[str]:
        url = repo_url or settings.default_repo_url
        return self.git.list_remote_branches(url)

    def get_history(self, task_id: int) -> list[TaskHistoryEntry]:
        rows = (
            self.db.query(TaskHistoryModel)
            .filter(TaskHistoryModel.task_id == task_id)
            .order_by(TaskHistoryModel.changed_at.desc())
            .all()
        )
        return [
            TaskHistoryEntry(
                id=r.id,
                task_id=r.task_id,
                field_name=r.field_name,
                old_value=r.old_value,
                new_value=r.new_value,
                changed_by=r.changed_by,
                changed_at=r.changed_at,
            )
            for r in rows
        ]

    def create_task(
        self,
        title: str,
        description: str | None,
        status: str,
        assigned_to: str | None,
        actor: str,
        repo_url: str | None = None,
        git_branch: str | None = None,
        create_git_branch: bool = False,
    ) -> Task:
        if status not in ALLOWED_STATUSES:
            raise HTTPException(422, "Недопустимый статус")
        now = datetime.now()
        repo = repo_url or settings.default_repo_url
        row = TaskModel(
            title=title,
            description=description or "Описание задачи",
            status=status,
            assigned_to=assigned_to,
            repo_url=repo,
            git_branch=git_branch,
            created_at=now,
            updated_at=now,
        )
        self.db.add(row)
        self.db.flush()

        if create_git_branch and not git_branch:
            try:
                branch = self.git.create_branch_for_task(repo, row.id, title)
                row.git_branch = branch
                self._log_change(row.id, "git_branch", None, branch, actor)
            except Exception as exc:
                raise HTTPException(400, f"Не удалось создать ветку Git: {exc}") from exc
        elif git_branch:
            self._log_change(row.id, "git_branch", None, git_branch, actor)

        self._log_change(row.id, "created", None, title, actor)
        self.db.commit()
        self.db.refresh(row)
        msg = f"Создана задача «{title}»"
        if row.git_branch:
            msg += f" (ветка {row.git_branch})"
        self.activity.record(ActivityType.TASK_CREATED, actor, msg, "task", row.id)
        return self._to_entity(row)

    def link_git_branch(
        self,
        task_id: int,
        git_branch: str | None,
        repo_url: str | None,
        create_git_branch: bool,
        actor: str,
    ) -> Task:
        row = self.db.get(TaskModel, task_id)
        if not row:
            raise HTTPException(404, "Задача не найдена")
        repo = repo_url or row.repo_url or settings.default_repo_url
        row.repo_url = repo
        old_branch = row.git_branch

        if create_git_branch:
            try:
                new_branch = self.git.create_branch_for_task(repo, row.id, row.title)
            except Exception as exc:
                raise HTTPException(400, f"Не удалось создать ветку: {exc}") from exc
            row.git_branch = new_branch
        elif git_branch:
            row.git_branch = git_branch.strip()
        else:
            raise HTTPException(422, "Укажите git_branch или create_git_branch=true")

        row.updated_at = datetime.now()
        self._log_change(task_id, "git_branch", old_branch, row.git_branch, actor)
        self.db.commit()
        self.db.refresh(row)
        self.activity.record(
            ActivityType.TASK_UPDATED,
            actor,
            f"Задача #{task_id} привязана к ветке {row.git_branch}",
            "task",
            task_id,
        )
        return self._to_entity(row)

    def update_task(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        status: str | None,
        assigned_to: str | None,
        git_branch: str | None,
        repo_url: str | None,
        actor: str,
    ) -> Task:
        row = self.db.get(TaskModel, task_id)
        if not row:
            raise HTTPException(404, "Задача не найдена")
        if status and status not in ALLOWED_STATUSES:
            raise HTTPException(422, "Недопустимый статус")

        changes = []
        if title is not None and title != row.title:
            changes.append(("title", row.title, title))
            row.title = title
        if description is not None and description != row.description:
            changes.append(("description", row.description, description))
            row.description = description
        if status is not None and status != row.status:
            changes.append(("status", row.status, status))
            row.status = status
        if assigned_to is not None and assigned_to != row.assigned_to:
            changes.append(("assigned_to", row.assigned_to, assigned_to))
            row.assigned_to = assigned_to
        if git_branch is not None and git_branch != row.git_branch:
            changes.append(("git_branch", row.git_branch, git_branch))
            row.git_branch = git_branch
        if repo_url is not None and repo_url != row.repo_url:
            changes.append(("repo_url", row.repo_url, repo_url))
            row.repo_url = repo_url

        row.updated_at = datetime.now()
        for field, old, new in changes:
            self._log_change(task_id, field, str(old) if old else None, str(new) if new else None, actor)
        self.db.commit()
        self.db.refresh(row)
        if changes:
            self.activity.record(
                ActivityType.TASK_UPDATED,
                actor,
                f"Обновлена задача #{task_id}",
                "task",
                task_id,
            )
        return self._to_entity(row)

    def move_task(self, task_id: int, status: str, actor: str) -> Task:
        if status not in ALLOWED_STATUSES:
            raise HTTPException(422, "Недопустимый статус")
        row = self.db.get(TaskModel, task_id)
        if not row:
            raise HTTPException(404, "Задача не найдена")
        if row.status == status:
            return self._to_entity(row)
        old_status = row.status
        row.status = status
        row.updated_at = datetime.now()
        self._log_change(task_id, "status", old_status, status, actor)
        self.db.commit()
        self.db.refresh(row)
        self.activity.record(
            ActivityType.TASK_MOVED,
            actor,
            f"Задача #{task_id}: {old_status} → {status}",
            "task",
            task_id,
        )
        return self._to_entity(row)

    def delete_task(self, task_id: int, actor: str) -> None:
        row = self.db.get(TaskModel, task_id)
        if not row:
            raise HTTPException(404, "Задача не найдена")
        title = row.title
        self.db.delete(row)
        self.db.commit()
        self.activity.record(
            ActivityType.TASK_DELETED,
            actor,
            f"Удалена задача «{title}»",
            "task",
            task_id,
        )
