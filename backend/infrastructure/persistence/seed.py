from datetime import datetime

from sqlalchemy.orm import Session

from config import settings
from infrastructure.persistence.models import TaskModel


def seed_database(db: Session) -> int:
    """Демо-задачи с привязкой к веткам, если таблица пуста."""
    if db.query(TaskModel).count() > 0:
        return 0

    now = datetime.now()
    repo = settings.default_repo_url
    samples = [
        ("Настроить CI pipeline", "todo", "olga.ivanova", "main"),
        ("API авторизации", "in_progress", "ivan.petrov", "task/2-api-avtorizacii"),
        ("Верстка Kanban", "done", "anna.smirnova", "task/3-verstka-kanban"),
    ]
    for title, status, assignee, branch in samples:
        db.add(
            TaskModel(
                title=title,
                description="Демо-задача (seed при старте)",
                status=status,
                assigned_to=assignee,
                git_branch=branch,
                repo_url=repo,
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()
    return len(samples)
