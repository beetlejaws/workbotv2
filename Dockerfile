FROM python:3.11-slim

# Устанавливаем poetry
RUN pip install --no-cache-dir poetry

# Рабочая директория
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock ./

# Ставим зависимости
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Копируем код
COPY . .

# Запуск бота
CMD ["poetry", "run", "python", "main.py"]