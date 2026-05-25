from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from domain.metrics.entities import MetricSample
from infrastructure.monitoring.collector import collect_metrics
from infrastructure.persistence.models import MetricSampleModel


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def collect_and_store(self) -> MetricSample:
        data = collect_metrics()
        row = MetricSampleModel(**data)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return MetricSample(
            id=row.id,
            host=row.host,
            cpu_percent=row.cpu_percent,
            memory_percent=row.memory_percent,
            memory_used_mb=row.memory_used_mb,
            memory_total_mb=row.memory_total_mb,
            process_count=row.process_count,
            top_processes=row.top_processes,
            recorded_at=row.recorded_at,
        )

    def get_latest(self) -> MetricSample | None:
        row = (
            self.db.query(MetricSampleModel)
            .order_by(MetricSampleModel.recorded_at.desc())
            .first()
        )
        if not row:
            return None
        return MetricSample(
            id=row.id,
            host=row.host,
            cpu_percent=row.cpu_percent,
            memory_percent=row.memory_percent,
            memory_used_mb=row.memory_used_mb,
            memory_total_mb=row.memory_total_mb,
            process_count=row.process_count,
            top_processes=row.top_processes,
            recorded_at=row.recorded_at,
        )

    def get_history(self, minutes: int = 30) -> list[MetricSample]:
        since = datetime.now() - timedelta(minutes=minutes)
        rows = (
            self.db.query(MetricSampleModel)
            .filter(MetricSampleModel.recorded_at >= since)
            .order_by(MetricSampleModel.recorded_at.asc())
            .all()
        )
        return [
            MetricSample(
                id=r.id,
                host=r.host,
                cpu_percent=r.cpu_percent,
                memory_percent=r.memory_percent,
                memory_used_mb=r.memory_used_mb,
                memory_total_mb=r.memory_total_mb,
                process_count=r.process_count,
                top_processes=r.top_processes,
                recorded_at=r.recorded_at,
            )
            for r in rows
        ]
