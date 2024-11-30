FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local'

# Install Poetry
RUN pip install poetry==1.8.4

# Copy dependency files first
COPY ./knyfe/pyproject.toml ./knyfe/poetry.lock /usr/src/app/

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root --no-cache

# Copy the application code
COPY ./knyfe /usr/src/app/

# Run the application
ENTRYPOINT ["./manage.py", "runserver", "0.0.0.0:8000"]
