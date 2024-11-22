FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/usr/src/app/.venv/bin:/usr/src/app:/root/.local/bin:$PATH

RUN python3 -m pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true

COPY ./knyfe /usr/src/app/
