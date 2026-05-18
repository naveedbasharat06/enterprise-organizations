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
    │   ├── components/        ← Shared components (AppLayout, App.vue)
    │   ├── store/             ← Vuex state management modules
    │   ├── router/            ← Vue Router (auth + role guards)
    │   └── api/               ← Axios API clients
    ├── Dockerfile
    └── nginx.conf             ← Nginx config (serves Vue + proxies /api/ + serves /media/)
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
| Frontend (Vue) | http://localhost:8080 |
| Backend API (Django) | http://localhost:8080/api/ |
| Django Admin | http://localhost:8080/admin/ |
| Media files (videos, PDFs) | http://localhost:8080/media/ |
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
| Authentication | JWT login/logout, refresh token rotation, 30-day sessions |
| Organizations | Multi-tenant orgs managed by Super Admin |
| Roles | Custom roles with assigned permissions per organization |
| Permissions | Fine-grained permission control (role-based + direct user permissions) |
| Users | Invite via email (7-day token), assign roles/permissions, promote/demote |
| My Access | Users can view all their assigned roles and direct permissions |
| Screen Recording | Record screen + mic in-browser via MediaRecorder API |
| File Upload | Upload MP4, WebM, MOV, MKV, MP3, WAV, M4A (up to 500 MB) |
| AI Transcription | Groq Whisper API (free, runs in background via Celery) |
| PDF Export | Professional timestamped transcript PDF (30-second blocks) |
| Password Reset | OTP via email (15-minute expiry) |
| Rate Limiting | Throttles on login (5/min), password reset (5/hr), invites (20/hr) |

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
- SimpleJWT (JWT authentication with refresh token rotation + blacklisting)
- Celery + Redis (background task processing)
- Groq Whisper API (AI speech-to-text transcription)
- imageio-ffmpeg (audio extraction from video files)
- ReportLab (PDF generation)
- SQLite (dev) / PostgreSQL (production)
- Gunicorn (WSGI server)

**Frontend**
- Vue.js 3 (Composition API with `<script setup>`)
- Vuex 4 (modular state management)
- Vue Router 4 (SPA routing with auth/role guards)
- Axios (HTTP client with auto token refresh interceptor)
- Vite (build tool)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy, Vue SPA serving, media file serving)
- Gunicorn (WSGI server)

---

## API Routes

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | JWT login |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| POST | `/api/auth/token/refresh/` | Get new access token |
| GET | `/api/auth/me/` | Current user profile |
| GET | `/api/auth/me/roles/` | Current user's roles |
| GET | `/api/auth/me/permissions/` | Current user's direct permissions |
| POST | `/api/auth/invite/` | Send email invitation |
| GET/POST | `/api/auth/accept-invitation/` | Accept invite + create account |
| POST | `/api/auth/forgot-password/` | Send OTP to email |
| POST | `/api/auth/reset-password-confirm/` | Verify OTP + reset password |

### Organizations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/organizations/` | List / create organizations |
| GET/PUT/DELETE | `/api/organizations/{id}/` | Retrieve / update / delete |
| GET | `/api/organizations/{id}/members/` | List org members |
| POST | `/api/organizations/{id}/add_member/` | Add member to org |
| POST | `/api/organizations/{id}/remove_member/` | Remove member from org |
| POST | `/api/organizations/{id}/toggle_recording/` | Enable/disable screen recording |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/users/` | List / create users |
| GET/PUT/DELETE | `/api/users/{id}/` | Retrieve / update / delete |
| GET | `/api/users/{id}/roles/` | User's assigned roles |
| POST | `/api/users/{id}/assign_role/` | Assign a role |
| POST | `/api/users/{id}/remove_role/` | Remove a role |
| GET | `/api/users/{id}/direct_permissions/` | User's direct permissions |
| POST | `/api/users/{id}/assign_permission/` | Assign a direct permission |
| POST | `/api/users/{id}/remove_permission/` | Remove a direct permission |
| POST | `/api/users/{id}/make_admin/` | Promote to Admin |
| POST | `/api/users/{id}/make_member/` | Demote to Member |

### Roles & Permissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/roles/` | List / create roles |
| GET/PUT/DELETE | `/api/roles/{id}/` | Retrieve / update / delete |
| POST | `/api/roles/{id}/assign_permissions/` | Set permissions for a role |
| GET/POST | `/api/permissions/` | List / create permissions |
| GET/PUT/DELETE | `/api/permissions/{id}/` | Retrieve / update / delete |

### Recordings & Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/recordings/` | List / upload recording |
| DELETE | `/api/recordings/{id}/` | Delete recording |
| GET | `/api/dashboard/stats/` | Role-scoped dashboard statistics |

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | `True` or `False` (default `False`) |
| `ALLOWED_HOSTS` | No | Comma-separated hostnames (default `localhost,127.0.0.1`) |
| `GROQ_API_KEY` | Yes | For AI transcription — free at https://console.groq.com |
| `EMAIL_HOST_USER` | Yes | Gmail address |
| `EMAIL_HOST_PASSWORD` | Yes | Gmail App Password |
| `FRONTEND_URL` | No | Used in invitation emails (default `http://localhost:5173`) |
| `DATABASE_URL` | No | Auto-set in Docker; for PostgreSQL: `postgresql://user:pass@host/db` |
| `CELERY_BROKER_URL` | No | Auto-set in Docker; for local: `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | No | Auto-set in Docker; for local: `redis://localhost:6379/0` |

---

## Security Notes

- **Access token** stored in-memory only (XSS-safe); never written to localStorage
- **Refresh token** stored in localStorage; rotates on every use with blacklisting
- **Token expiry**: access token 1 hour, refresh token 30 days
- **OTP expiry**: password reset OTPs expire after 15 minutes
- **Invitation expiry**: invite tokens expire after 7 days
- **Rate limiting**: login (5/min), password reset (5/hr), invitations (20/hr)
- **Queryset-level isolation**: each API viewset filters data by the requesting user's role and organization
