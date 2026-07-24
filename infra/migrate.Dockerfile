FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir asyncpg==0.30.0

COPY infra/migrations ./infra/migrations
COPY scripts/run_migrations.py ./scripts/run_migrations.py

CMD ["python", "scripts/run_migrations.py"]
