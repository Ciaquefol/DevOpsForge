# infra/Dockerfile.frontend
FROM node:20-alpine

WORKDIR /app

# Копирование package.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm install

# Копирование исходного кода
COPY frontend/ .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]