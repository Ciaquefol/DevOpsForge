set -e

echo "Starting DevOpsForge deployment..."

cd "$(dirname "$0")/.."

# Загрузка переменных окружения
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Остановка старых контейнеров
echo "Stopping old containers..."
docker-compose down

# Сборка и запуск
echo "Building and starting services..."
docker-compose up -d --build

# Ожидание готовности БД
echo "Waiting for database..."
sleep 10

# Проверка статуса
echo "Checking services status..."
docker-compose ps

echo "Deployment completed!"
echo " Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000/docs"
echo "   Database: localhost:5432"