# DevOpsForge

Платформа мониторинга команды разработки: Kanban с историей изменений, real-time активность, автодеплой с rollback, история развёртываний и метрики серверов.

## Возможности

| Подсистема | Описание |
|------------|----------|
| **Kanban** | CRUD задач, drag-and-drop статусов, история изменений (`/api/tasks/{id}/history`) |
| **Активность** | Лента событий + WebSocket `/api/ws/activity` |
| **Деплой** | Git clone → Docker build → run; история в `/api/deployments` |
| **Rollback** | `POST /api/deployments/{id}/rollback` |
| **Метрики** | CPU, RAM, процессы; REST + WebSocket `/api/ws/metrics` |
| **Prometheus** | `GET /metrics/prometheus` |

Для деплоя нужен Docker Desktop (доступ к `docker.sock` в compose).
