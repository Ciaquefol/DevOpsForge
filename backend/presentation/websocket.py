import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from infrastructure.activity.broadcaster import broadcaster

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/activity")
async def activity_ws(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)


@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    from infrastructure.persistence.database import SessionLocal
    from application.metrics.service import MetricsService

    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                service = MetricsService(db)
                sample = service.collect_and_store()
                payload = {
                    "host": sample.host,
                    "cpu_percent": sample.cpu_percent,
                    "memory_percent": sample.memory_percent,
                    "memory_used_mb": sample.memory_used_mb,
                    "memory_total_mb": sample.memory_total_mb,
                    "process_count": sample.process_count,
                    "top_processes": json.loads(sample.top_processes),
                    "recorded_at": sample.recorded_at.isoformat(),
                }
                await websocket.send_json(payload)
            finally:
                db.close()
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
