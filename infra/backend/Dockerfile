FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /app/deploy_workspace /app/logs

ENV SEED_ON_STARTUP=true
ENV DEPLOY_WORKSPACE=/app/deploy_workspace
ENV GIT_CACHE_DIR=/app/deploy_workspace/git-cache

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
