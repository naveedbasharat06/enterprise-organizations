# RoleBase Dashboard

A multi-tenant role-based access control dashboard built with **Django REST Framework** + **Vue.js 3**.

Supports three roles — **Super Admin**, **Admin**, and **Member** — with organizations, custom roles, permissions, user invitations, screen recording, and AI transcription.

---

## Project Structure

```
project/
├── docker-compose.yml         ← runs everything with one command
├── backend/
│   ├── core/                  ← Django project (settings, urls, celery)
│   ├── accounts/              ← Main app (models, views, tasks, permissions)
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── .env.example           ← copy to .env and fill in your values
└── frontend/
    ├── src/
    │   ├── views/             ← Vue pages (Dashboard, Users, Roles, etc.)
    │   ├── store/             ← Vuex state management
    │   ├── router/            ← Vue Router
    │   └── api/               ← Axios API calls
    ├── Dockerfile
    └── nginx.conf             ← Nginx config (serves Vue + proxies /api/)
```

---

## Running with Docker (Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### 1. Set up environment variables
```bash
cd backend
copy .env.example .env
```
Edit `backend/.env` and fill in your values:
- `SECRET_KEY` — any long random string
- `GROQ_API_KEY` — get free at https://console.groq.com
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — Gmail + App Password

### 2. Start everything
```bash
# From the project root
docker compose up --build
```

That's it. All 4 services start together:

| Service | URL |
|---------|-----|
| Frontend (Vue) | http://localhost |
| Backend (Django) | http://localhost/api/ |
| Django Admin | http://localhost/admin/ |
| Redis | internal only |

### 3. Stop everything
```bash
docker compose down
```

### Useful Docker commands
```bash
# Rebuild after code changes
docker compose up --build

# View logs
docker compose logs -f

# View logs for one service
docker compose logs -f backend
docker compose logs -f celery

# Open Django shell inside container
docker compose exec backend python manage.py shell

# Create a superuser
docker compose exec backend python manage.py createsuperuser

# Run migrations manually
docker compose exec backend python manage.py migrate
```

---

## Running Locally (Without Docker)

You need **4 terminals** running simultaneously.

### Terminal 1 — Redis
```bash
# Start your Redis container (if using Docker for Redis only)
docker start redis
```

### Terminal 2 — Django Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# → http://localhost:8000
```

### Terminal 3 — Celery Worker
```bash
cd backend
venv\Scripts\activate
celery -A core worker --loglevel=info --pool=solo
# --pool=solo is required on Windows
```

### Terminal 4 — Vue Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Features

| Feature | Description |
|---------|-------------|
| Authentication | JWT login/logout, refresh tokens, 30-day sessions |
| Organizations | Multi-tenant orgs managed by Super Admin |
| Roles | Custom roles with assigned permissions |
| Permissions | Fine-grained permission control |
| Users | Invite via email, assign roles/permissions |
| Screen Recording | Record screen + mic, upload video |
| AI Transcription | Groq Whisper API (free, runs in background via Celery) |
| PDF Export | Professional timestamped transcript PDF |
| Password Reset | OTP via email |

---

## Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| superadmin | Admin@1234 | Super Admin |
| (org admins) | Admin@1234 | Admin |
| (members) | Admin@1234 | Member |

---

## Tech Stack

**Backend**
- Django 4.x + Django REST Framework
- SimpleJWT (authentication)
- Celery + Redis (background tasks)
- Groq Whisper API (transcription)
- imageio-ffmpeg (audio extraction)
- ReportLab (PDF generation)
- SQLite (dev) / PostgreSQL (production)

**Frontend**
- Vue.js 3 (Composition API)
- Vuex (state management)
- Vue Router
- Axios (HTTP client)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy + static file serving)
- Gunicorn (WSGI server)

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | True/False (default False) |
| `GROQ_API_KEY` | Yes | For AI transcription |
| `EMAIL_HOST_USER` | Yes | Gmail address |
| `EMAIL_HOST_PASSWORD` | Yes | Gmail App Password |
| `DATABASE_URL` | No | Auto-set in Docker |
| `CELERY_BROKER_URL` | No | Auto-set in Docker |
