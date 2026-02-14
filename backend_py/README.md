## Python Backend for AI Interviewer

This directory contains the FastAPI backend used by the frontend app.

## Stack

- FastAPI (API server)
- TiDB/MySQL (database)
- Cloudinary (file storage)
- Redis + RQ (background jobs)
- OpenAI (AI evaluation)
- Mailgun (email)

## Setup

```bash
cd backend_py
python -m venv .venv
source .venv/Scripts/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment Variables

Use either `DATABASE_URL` or `DB_*` values.

```env
PORT=3001
NODE_ENV=development

APP_URL=http://localhost:3000
FRONTEND_URL=http://localhost:3000

# Preferred
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>

# Optional fallback when DATABASE_URL is empty
DB_NAME=ai_interview
DB_USER=<user>
DB_PASSWORD=<password>
DB_HOST=127.0.0.1
DB_PORT=3306

# Optional DB TLS flags
DB_SSL_ENABLED=true
DB_SSL_VERIFY_CERT=true
DB_SSL_VERIFY_IDENTITY=true
DB_SSL_CA=

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=your_mailgun_domain
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME=AI Interviewer

REDIS_HOST=127.0.0.1
REDIS_PORT=6379

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```

## Database Migrations (SQL-first)

Migrations are versioned SQL files in:

- `app/tidb/migrations/`

Applied migrations are tracked in DB table:

- `schema_migrations`

Commands:

```bash
cd backend_py
python migrate.py status
python migrate.py up
python migrate.py new add_transcript_index
```

Migration workflow for future DB changes:

1. Create new migration file: `python migrate.py new <name>`
2. Add forward-only SQL (`ALTER TABLE`, `CREATE INDEX`, etc.)
3. Apply pending migrations: `python migrate.py up`
4. Commit migration file to git

Rules:

- Do not edit previously applied migration files.
- Create a new migration for each schema change.
- `app/tidb/schema.sql` is a bootstrap snapshot, not the migration history.

## Run API

```bash
cd backend_py
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Health endpoint:

- `GET http://localhost:3001/health`

## Run Worker

```bash
cd backend_py
python run_worker.py
```

## Notes

- Trailing slash redirects (`307`) from `/api/jobs` to `/api/jobs/` are normal in FastAPI.
- For TiDB Cloud Serverless, use TLS and the correct prefixed username from TiDB Cloud connection details.
