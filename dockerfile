FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /crawlerjus
ENV PYTHONPATH=/crawlerjus


RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*


ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" \
 && poetry config virtualenvs.create false


COPY pyproject.toml poetry.lock* /crawlerjus/


ARG ENV=prod
RUN if [ "$ENV" = "dev" ]; then \
      poetry install --no-interaction --no-ansi ; \
    else \
      poetry install --no-interaction --no-ansi --only main ; \
    fi

RUN poetry config virtualenvs.create false \
&& poetry install --no-interaction --no-ansi --only main

COPY . /crawlerjus

EXPOSE 8000

CMD ["uvicorn", "api.router:app", "--host", "0.0.0.0", "--port", "8000"]