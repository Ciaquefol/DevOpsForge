from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MetricSample:
    id: Optional[int]
    host: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    process_count: int
    top_processes: str
    recorded_at: datetime
