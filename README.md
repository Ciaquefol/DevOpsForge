# DevOpsForge

Платформа мониторинга команды разработки: Kanban с историей изменений, real-time активность, автодеплой с rollback, история развёртываний и метрики серверов.

**Полная инструкция пользователя:** [INSTRUCTION.md](INSTRUCTION.md) (установка, запуск, все вкладки, деплой, troubleshooting).

**Сценарий для защиты (по шагам, что нажимать и что говорить):** [DEMO_SCRIPT.md](DEMO_SCRIPT.md)  
**Краткая шпаргалка:** [PRESENTATION.md](PRESENTATION.md)

## Архитектура (DDD)

```
backend/
  domain/           # Сущности и правила (Task, Deployment, Metric, Activity)
  application/      # Use cases (сервисы)
  infrastructure/ # БД, Git, Docker, psutil, WebSocket broadcaster
  presentation/     # FastAPI routers, WebSocket, schemas
```

## Возможности

| Подсистема | Описание |
|------------|----------|
| **Kanban** | CRUD задач, drag-and-drop статусов, история изменений (`/api/tasks/{id}/history`) |
| **Активность** | Лента событий + WebSocket `/api/ws/activity` |
| **Деплой** | Git clone → Docker build → run; история в `/api/deployments` |
| **Rollback** | `POST /api/deployments/{id}/rollback` |
| **Метрики** | CPU, RAM, процессы; REST + WebSocket `/api/ws/metrics` |
| **Prometheus** | `GET /metrics/prometheus` |

## Быстрый старт (Windows)

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

```bat
cd frontend
npm install
npm run dev
```

Или из корня: `start_all.bat`

- UI: http://127.0.0.1:5173
- API docs: http://127.0.0.1:8000/docs

## Docker

```bash
cd infra
cp .env.example .env   # при необходимости
./scripts/deploy.sh
```

- http://localhost — nginx
- http://localhost:8000/docs — API

## Переменные окружения

См. `backend/.env.example` и `infra/.env.example`.

`DATABASE_URL` — SQLite локально (`sqlite:///./tasks.db`) или PostgreSQL в Docker.

## API (префикс `/api`)

- `GET/POST /api/tasks`, `PATCH /api/tasks/{id}/move`, `GET /api/tasks/{id}/history`
- `GET/POST /api/deployments`, `POST /api/deployments/{id}/rollback`
- `GET /api/metrics/latest`, `GET /api/metrics/history`
- `GET /api/activity`

Для деплоя нужен Docker Desktop (доступ к `docker.sock` в compose).
