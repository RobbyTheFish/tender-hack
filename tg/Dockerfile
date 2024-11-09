# telegram_bot/Dockerfile

FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /bot

# Копируем файлы зависимостей
COPY telegram_bot/requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем исходный код бота
COPY telegram_bot/ .

# Открываем порт
EXPOSE 80

# Команда для запуска бота
CMD ["python", "bot.py"]
