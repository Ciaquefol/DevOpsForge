#!/usr/bin/env bash
set -e

echo "Starting DevOpsForge deployment..."

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "Stopping old containers..."
docker compose down

echo "Building and starting services..."
docker compose up -d --build

echo "Waiting for database..."
sleep 12

echo "Checking services status..."
docker compose ps

echo ""
echo "Deployment completed!"
echo "  UI (nginx):     http://localhost"
echo "  Frontend:       http://localhost:5173"
echo "  Backend API:    http://localhost:8000/docs"
echo "  Health:         http://localhost:8000/health"
