# Deployment Guide 

This guide outlines how to deploy the LLM Inference Gateway to a production environment.

## 1. Environment Variables

Ensure the following variables are set in your production environment (e.g., Vercel, Railway, Heroku, AWS Secrets):

| Variable         | Description                              | Example                                       |
| ---------------- | ---------------------------------------- | --------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL Connection String             | `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY`     | Secret for JWT signing                   | `openssl rand -hex 32`                        |
| `OPENAI_API_KEY` | Key for OpenAI Provider                  | `sk-...`                                      |
| `GEMINI_API_KEY` | Key for Google Gemini                    | `AIza...`                                     |
| `REDIS_URL`      | (Optional) For distributed rate limiting | `redis://host:6379/0`                         |
| `OPENAI_TIMEOUT` | Timeout in seconds                       | `30`                                          |

## 2. Vercel: Serverless Data Extraction

The recommended architecture for high scalability is **Vercel** for the API/Extraction/Frontend layer and a dedicated **Cloud Database** (Neon/Supabase) for storage.

This approach ensures:

- **Separation of Concerns**: The extraction logic (API) scales to zero independently of the storage.
- **Zero Access Exposure**: The API extracts data via secure connection strings (Env Vars), but the database itself is never directly exposed to the internet.

### Configuration

1.  **Frontend/API**: Included in this repo (`frontend/` + `api/index.py`).
2.  **Routing**: `vercel.json` maps API calls to Python functions and static assets to CDN.

### Deployment Steps

1.  **Install Vercel CLI**: `npm i -g vercel`
2.  **Deploy**:
    ```bash
    vercel
    ```
3.  **Secure Connection**:
    - In Vercel Dashboard, go to **Settings > Environment Variables**.
    - Add your `DATABASE_URL` (from Neon/Supabase). This is the _only_ link between the extraction layer and the storage.

> **Note**: Vercel functions are ephemeral. You must run database migrations (table creation) externally or via a one-off script, as the function itself handles _runtime extraction_, not _schema management_.

## 3. Docker Deployment (Containerized)

For a self-contained deployment (e.g. AWS EC2, DigitalOcean):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Run:**

```bash
docker run -p 8000:8000 --env-file .env llm-gateway
```

## 4. Scaling Logic

- **Extraction Layer (Vercel)**: Automatically scales to 1,000+ concurrent extractions.
- **Storage Layer (DB)**: Use a connection pooler (PgBouncer) on your DB provider to handle the influx of extraction requests.
