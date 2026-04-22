FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка дополнительных пакетов для мониторинга
RUN pip install psutil docker prometheus-client

# Копирование кода
COPY backend/ .

# Создание директории для логов
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]