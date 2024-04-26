# Используем базовый образ Python
FROM python:3.9-alpine

# Установка приложения и его зависимостей
WORKDIR /app
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения внутрь контейнера
COPY . /app

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]