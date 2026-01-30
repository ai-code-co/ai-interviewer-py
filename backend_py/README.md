<!-- backend_py/README.md -->
## Python Backend for AI Interviewer

This directory contains a **FastAPI-based Python backend** that mirrors the existing Node/Express API in `backend/`.

The goals of this Python backend are:

- Preserve the **same REST API surface** used by the frontend:
  - `GET /health`
  - `GET /api/jobs`, `GET /api/jobs/:id`, `POST /api/jobs`, `PUT /api/jobs/:id`, `DELETE /api/jobs/:id`
  - `POST /api/invites`, `GET /api/invites`, `GET /api/invites/public/jobs`
  - `GET /api/candidates`, `GET /api/candidates/:id`, `PUT /api/candidates/:id/status`
  - `GET /api/apply/validate`, `POST /api/apply/submit`
- Keep the **same infrastructure dependencies**:
  - Supabase (DB + Storage)
  - Redis for background jobs
  - OpenAI for AI evaluations
  - Mailgun for email
- Provide an **asynchronous AI evaluation pipeline** using a Redis-backed worker.

The original Node backend is left untouched in `backend/` so you can switch between them if needed.

---

## Requirements

Python 3.10+ is recommended.

Install dependencies:

```bash
cd backend_py
python -m venv .venv
source .venv/Scripts/activate  # on Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy your existing backend `.env` file (or create a new one) so the Python backend uses the same configuration:

```bash
cp ../backend/.env .env  # or create .env manually
```

Required environment variables (same as Node backend):

```env
PORT=3001
NODE_ENV=development

SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=your_mailgun_domain
MAIL_FROM_ADDRESS=noreply@yourdomain.com
MAIL_FROM_NAME=admin

APP_URL=http://localhost:3000
CORS_ORIGIN=http://localhost:3000

REDIS_HOST=127.0.0.1
REDIS_PORT=6379

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

---

## Running the API

From `backend_py/`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Health check:

- `GET http://localhost:3001/health`

The OpenAPI docs are available at:

- Swagger UI: `http://localhost:3001/docs`
- ReDoc: `http://localhost:3001/redoc`

---

## Running the AI Evaluation Worker

The AI evaluation is handled by a Redis-backed RQ worker that processes jobs from the `ai-evaluation` queue.

Start Redis (same as the Node backend) and then run:

```bash
cd backend_py
python run_worker.py 
``` 

The worker will:

1. Download resumes from Supabase Storage
2. Extract text from PDF/DOC/DOCX
3. Fetch job details from Supabase
4. Call OpenAI for evaluation
5. Save results to the `ai_evaluations` table

---

## Project Structure

```text
backend_py/
├── app/
│   ├── main.py                # FastAPI app, routes, and health check
│   ├── config.py              # Environment + Supabase + Redis config
│   ├── queue.py               # RQ queue setup
│   ├── routes/
│   │   ├── jobs.py            # /api/jobs endpoints
│   │   ├── invites.py         # /api/invites endpoints
│   │   ├── candidates.py      # /api/candidates endpoints
│   │   └── apply.py           # /api/apply endpoints + file upload
│   ├── services/
│   │   ├── ai_evaluation_service.py  # OpenAI + evaluation persistence
│   │   ├── email_service.py          # Mailgun integration
│   │   ├── resume_parser_service.py  # PDF/DOCX parsing
│   │   └── storage_service.py        # Supabase Storage helpers
│   └── workers/
│       └── ai_evaluation_worker.py   # Job processing function used by RQ
├── requirements.txt
└── README.md
```

---

## Notes

- The Python backend is designed to be **API-compatible** with the Node backend so the existing frontend can continue to work.
- Error messages and validation rules are kept as close as possible to the Node version.
- Retries and backoff for the AI evaluation jobs are handled by RQ’s own retry mechanisms (configurable per job).

