FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/crawlerjus

WORKDIR /crawlerjus

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gcc \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.4.0

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./

ARG ENV=prod

RUN if [ "$ENV" = "dev" ]; then \
        poetry install --no-interaction --no-ansi --no-root; \
    else \
        poetry install --no-interaction --no-ansi --only main --no-root; \
    fi

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --chown=app:app . .

USER app

EXPOSE 8000

CMD ["uvicorn", "api.router:app", "--host", "0.0.0.0", "--port", "8000"]