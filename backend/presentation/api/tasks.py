from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.tasks.service import TaskService
from infrastructure.persistence.database import get_db
from presentation.schemas import (
    TaskCreateSchema,
    TaskHistorySchema,
    TaskLinkBranchSchema,
    TaskMoveSchema,
    TaskSchema,
    TaskUpdateSchema,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_to_schema(task) -> TaskSchema:
    return TaskSchema(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        assigned_to=task.assigned_to,
        git_branch=task.git_branch,
        repo_url=task.repo_url,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=list[TaskSchema])
def list_tasks(db: Session = Depends(get_db)):
    service = TaskService(db)
    return [_task_to_schema(t) for t in service.list_tasks()]


@router.get("/{task_id}/history", response_model=list[TaskHistorySchema])
def task_history(task_id: int, db: Session = Depends(get_db)):
    service = TaskService(db)
    return [
        TaskHistorySchema(
            id=h.id,
            task_id=h.task_id,
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            changed_by=h.changed_by,
            changed_at=h.changed_at,
        )
        for h in service.get_history(task_id)
    ]


@router.post("", response_model=TaskSchema)
def create_task(payload: TaskCreateSchema, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.create_task(
        payload.title,
        payload.description,
        payload.status,
        payload.assigned_to,
        payload.actor,
        payload.repo_url,
        payload.git_branch,
        payload.create_git_branch,
    )
    return _task_to_schema(task)


@router.put("/{task_id}", response_model=TaskSchema)
def update_task(task_id: int, payload: TaskUpdateSchema, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.update_task(
        task_id,
        payload.title,
        payload.description,
        payload.status,
        payload.assigned_to,
        payload.git_branch,
        payload.repo_url,
        payload.actor,
    )
    return _task_to_schema(task)


@router.patch("/{task_id}/git-branch", response_model=TaskSchema)
def link_git_branch(task_id: int, payload: TaskLinkBranchSchema, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.link_git_branch(
        task_id,
        payload.git_branch,
        payload.repo_url,
        payload.create_git_branch,
        payload.actor,
    )
    return _task_to_schema(task)


@router.patch("/{task_id}/move", response_model=TaskSchema)
def move_task(task_id: int, payload: TaskMoveSchema, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.move_task(task_id, payload.status, payload.actor)
    return _task_to_schema(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, actor: str = "system", db: Session = Depends(get_db)):
    service = TaskService(db)
    service.delete_task(task_id, actor)
    return {"ok": True, "message": f"Задача {task_id} удалена"}
