from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.metrics.service import MetricsService
from infrastructure.persistence.database import get_db
from presentation.schemas import MetricSampleSchema, parse_top_processes

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _to_schema(m) -> MetricSampleSchema:
    return MetricSampleSchema(
        id=m.id,
        host=m.host,
        cpu_percent=m.cpu_percent,
        memory_percent=m.memory_percent,
        memory_used_mb=m.memory_used_mb,
        memory_total_mb=m.memory_total_mb,
        process_count=m.process_count,
        top_processes=parse_top_processes(m.top_processes),
        recorded_at=m.recorded_at,
    )


@router.get("/latest", response_model=MetricSampleSchema | None)
def latest_metrics(db: Session = Depends(get_db)):
    service = MetricsService(db)
    sample = service.get_latest()
    return _to_schema(sample) if sample else None


@router.get("/history", response_model=list[MetricSampleSchema])
def metrics_history(minutes: int = 30, db: Session = Depends(get_db)):
    service = MetricsService(db)
    return [_to_schema(m) for m in service.get_history(minutes)]


@router.post("/collect", response_model=MetricSampleSchema)
def collect_now(db: Session = Depends(get_db)):
    service = MetricsService(db)
    return _to_schema(service.collect_and_store())
