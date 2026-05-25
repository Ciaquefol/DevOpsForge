import json
import socket
from datetime import datetime

import psutil


def collect_metrics() -> dict:
    mem = psutil.virtual_memory()
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            if info.get("cpu_percent") is not None:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda p: (p.get("cpu_percent") or 0), reverse=True)
    top = processes[:10]
    return {
        "host": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / (1024 * 1024), 2),
        "memory_total_mb": round(mem.total / (1024 * 1024), 2),
        "process_count": len(psutil.pids()),
        "top_processes": json.dumps(top, default=str),
        "recorded_at": datetime.now(),
    }
