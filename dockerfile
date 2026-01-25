FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /crawlerjus
ENV PYTHONPATH=/crawlerjus

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libcurl4 \
    libcurl4-openssl-dev \
    openssl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
ARG ENV=prod

RUN if [ "$ENV" = "dev" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt ; \
    else \
        pip install --no-cache-dir -r requirements.txt ; \
    fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.router:app", "--host", "0.0.0.0", "--port", "8000"]