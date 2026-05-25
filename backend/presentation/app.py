import asyncio
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from config import settings
from infrastructure.activity.broadcaster import broadcaster
from infrastructure.persistence.database import SessionLocal, init_db
from presentation.api import activity, bootstrap, deployments, git, metrics, tasks
from infrastructure.bootstrap.container_seed import seed_container_workspace
from infrastructure.persistence.seed import seed_database
from presentation.websocket import router as ws_router


def _metrics_collector_loop():
    from application.metrics.service import MetricsService

    while True:
        try:
            db = SessionLocal()
            try:
                MetricsService(db).collect_and_store()
            finally:
                db.close()
        except Exception:
            pass
        time.sleep(settings.metrics_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_container_workspace()
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    loop = asyncio.get_event_loop()
    broadcaster.set_loop(loop)
    collector = threading.Thread(target=_metrics_collector_loop, daemon=True)
    collector.start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DevOpsForge API",
        description="Мониторинг команды, Kanban, автодеплой и метрики",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from fastapi import APIRouter

    api_router = APIRouter(prefix="/api")
    api_router.include_router(tasks.router)
    api_router.include_router(git.router)
    api_router.include_router(bootstrap.router)
    api_router.include_router(deployments.router)
    api_router.include_router(metrics.router)
    api_router.include_router(activity.router)
    app.include_router(api_router)
    app.include_router(ws_router, prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "environment": settings.environment}

    @app.get("/metrics/prometheus")
    def prometheus_metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
