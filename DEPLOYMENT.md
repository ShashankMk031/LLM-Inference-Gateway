# Deployment Guide 

This guide outlines how to deploy the LLM Inference Gateway to a production environment.

## 1. Environment Variables

Ensure the following variables are set in your production environment (e.g., Railway, Heroku, AWS Secrets):

| Variable         | Description                              | Example                                       |
| ---------------- | ---------------------------------------- | --------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL Connection String             | `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY`     | Secret for JWT signing                   | `openssl rand -hex 32`                        |
| `OPENAI_API_KEY` | Key for OpenAI Provider                  | `sk-...`                                      |
| `GEMINI_API_KEY` | Key for Google Gemini                    | `AIza...`                                     |
| `REDIS_URL`      | (Optional) For distributed rate limiting | `redis://host:6379/0`                         |

## 2. Docker Deployment (Recommended)

Create a `Dockerfile` in the root (if not present):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Build and Run:**

```bash
docker build -t llm-gateway .
docker run -p 8000:8000 --env-file .env llm-gateway
```

## 3. Database Migrations

This project uses SQLAlchemy `Base.metadata.create_all` for simplicity in `app/main.py`.
For production, it is recommended to init **Alembic**:

1. `alembic init alembic`
2. Update `alembic.ini` with DB URL.
3. Import models in `env.py`.
4. Run `alembic revision --autogenerate -m "Initial"`
5. Run `alembic upgrade head`

## 4. Health Checks

Configure your load balancer (e.g., AWS ALB) to check:

- **Path**: `/health`
- **Expected Status**: `200 OK`
- **Body**: `{"status": "healthy"}`

## 5. Scaling

- **Horizontal**: Deploy multiple replicas of the Docker container.
- **Vertical**: Increase CPU for JSON parsing/validation heavy loads.
- **Database**: Use a managed RDS/Postgres with connection pooling (PgBouncer) if connections exceed 100.
