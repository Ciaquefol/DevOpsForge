from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_columns():
    """Добавляет новые колонки в существующую БД (SQLite/Postgres)."""
    from infrastructure.persistence import models  # noqa: F401

    inspector = inspect(engine)
    if "tasks" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("tasks")}
        alters = []
        if "git_branch" not in existing:
            alters.append("ALTER TABLE tasks ADD COLUMN git_branch VARCHAR(255)")
        if "repo_url" not in existing:
            alters.append("ALTER TABLE tasks ADD COLUMN repo_url VARCHAR(512)")
        if alters:
            with engine.begin() as conn:
                for sql in alters:
                    conn.execute(text(sql))

    if "deployments" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("deployments")}
        if "task_id" not in existing:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE deployments ADD COLUMN task_id INTEGER"))


def init_db():
    from infrastructure.persistence import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_columns()
