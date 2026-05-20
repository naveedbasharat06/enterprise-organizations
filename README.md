# RoleBase Dashboard

A multi-tenant role-based access control (RBAC) dashboard built with **Django REST Framework** + **Vue.js 3**.

Supports three roles — **Super Admin**, **Admin**, and **Member** — with organizations, custom roles, permissions, user invitations, screen recording, AI transcription, and **Stripe subscription billing**.

---

## Installation Guide (First Time Setup)

Follow these steps in order the very first time you run the project.

### Step 1 — Install Docker Desktop

Download and install from: https://www.docker.com/products/docker-desktop/

After installing, open Docker Desktop and make sure it is **running** (green icon in system tray).

### Step 2 — Get the project

If you received a zip file, extract it. If you are cloning from Git:
```bash
git clone <repository-url>
cd project
```

### Step 3 — Create your environment file

Open a terminal in the `project` folder and run:
```bash
cd backend
copy .env.example .env
```

Now open `backend/.env` in any text editor and fill in these values:

```env
SECRET_KEY=any-long-random-string-change-this
DEBUG=True
GROQ_API_KEY=your-groq-api-key-here
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
FRONTEND_URL=http://localhost:8080
```

**Where to get these values:**
- `SECRET_KEY` — type any random characters, e.g. `my-secret-key-abc123xyz456`
- `GROQ_API_KEY` — sign up free at https://console.groq.com → API Keys → Create key
- `EMAIL_HOST_PASSWORD` — this is a **Gmail App Password**, not your regular Gmail password. To get one:
  1. Go to your Google Account → Security
  2. Enable 2-Step Verification (required)
  3. Go to Security → App Passwords
  4. Create a new app password → copy the 16-character code
- `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` — create a free test account at https://stripe.com → Developers → API keys

### Step 4 — Start the application

Go back to the `project` root folder and run:
```bash
docker compose up --build
```

Wait for all 4 services to start. You will see lines like:
```
backend   | >>> Running database migrations...
backend   | >>> Seeding initial data (super admin + sample orgs)...
backend   | ✓ Super Admin created: superadmin / Admin@1234
```

### Step 5 — Set up Stripe products (one-time)

After the containers are running, run this command once to create all subscription products and prices in your Stripe account:
```bash
docker compose exec backend python manage.py setup_stripe
```

This will print 9 price IDs. Copy them into `backend/.env`:
```env
STRIPE_BASIC_MONTHLY_PRICE_ID=price_...
STRIPE_BASIC_ANNUAL_PRICE_ID=price_...
STRIPE_BASIC_METERED_PRICE_ID=price_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_ANNUAL_PRICE_ID=price_...
STRIPE_PRO_METERED_PRICE_ID=price_...
STRIPE_PREMIUM_MONTHLY_PRICE_ID=price_...
STRIPE_PREMIUM_ANNUAL_PRICE_ID=price_...
STRIPE_PREMIUM_METERED_PRICE_ID=price_...
```

Then rebuild:
```bash
docker compose up --build -d
```

### Step 6 — Open the app

Go to: **http://localhost:8080**

Log in with the default Super Admin account (see below).

> The first build takes 3–5 minutes to download all dependencies. Subsequent starts are much faster.

---

## Default Login Credentials

These accounts are created automatically on first run:

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `superadmin` | `Admin@1234` | Super Admin | Full platform access — manages all organizations |
| `admin_tech` | `Admin@1234` | Admin | Manages Tech Corp organization |
| `john_member` | `Admin@1234` | Member | Basic member account |

> **Important:** Change the `superadmin` password after first login in a production environment.

---

## User Roles Explained

RoleBase has two distinct types of administrators:

### Platform Super Admin (`superadmin`)
- The developer or system administrator who runs the application
- Has **no organization** — sits above all organizations
- Can see and manage **every** organization, user, role, and permission on the platform
- Created once via `seed_data.py` — not available through self-signup
- Think of this as the person who owns the server

### Organization Admin (created via Stripe onboarding)
- A **customer** who paid for a subscription and created their own organization
- Scoped entirely to **their own organization** — cannot see other organizations
- Can manage members, roles, and permissions within their org
- Created automatically when Stripe checkout completes

### Admin (invited by org admin)
- Helps the org admin manage their organization
- Same scope as org admin — limited to their own organization

### Member
- Regular user within an organization
- Can only view their own profile, roles, and permissions

---

## Subscription Plans

New organizations sign up through the `/pricing` or `/onboarding` pages and pay via Stripe.

| Plan | Monthly | Annual | Storage | Recording |
|------|---------|--------|---------|-----------|
| Basic | $20/mo | $192/yr | 5 GB | No |
| Professional | $40/mo | $384/yr | 20 GB | Yes |
| Premium | $80/mo | $768/yr | 50 GB | Yes |

**Storage overage** is billed automatically through Stripe metered billing:
- Basic: $5/GB over quota
- Professional: $4/GB over quota
- Premium: $3/GB over quota

---

## Organization Onboarding Flow

1. Visit **`/pricing`** → choose a plan → click Get Started
2. Fill in the **3-step onboarding form** at `/onboarding`:
   - Step 1: Organization name, industry, size
   - Step 2: Admin account (username, email, password)
   - Step 3: Plan selection and billing cycle (monthly or annual)
3. Redirected to **Stripe hosted checkout** — enter card details
4. After payment, redirected to **`/onboarding/success`**
5. Organization and admin account are created automatically
6. Log in with the credentials entered during signup

**Test card for Stripe (test mode):** `4242 4242 4242 4242` — any future expiry, any CVC

---

## Project Structure

```
project/
├── docker-compose.yml              ← runs everything with one command
├── backend/
│   ├── core/                       ← Django project (settings, urls, celery)
│   ├── accounts/                   ← Users, orgs, roles, permissions, recording
│   │   ├── models.py               ← Organization, User, Role, Permission, Recording, StorageUsage
│   │   ├── views.py                ← All API viewsets and auth views
│   │   ├── tasks.py                ← Celery tasks (transcription + storage tracking)
│   │   └── permissions.py          ← IsSuperAdmin, IsAdminOrSuperAdmin, CanUseRecording
│   ├── payments/                   ← Stripe billing and subscription management
│   │   ├── views.py                ← Checkout, webhook, verify-session, storage usage
│   │   ├── stripe_utils.py         ← Stripe API helpers, plan config, meter events
│   │   └── management/commands/
│   │       └── setup_stripe.py     ← One-time command to create Stripe products/prices
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── .env.example                ← copy to .env and fill in your values
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── PricingView.vue     ← Public pricing page (/pricing)
    │   │   ├── OnboardingView.vue  ← 3-step signup form (/onboarding)
    │   │   ├── OnboardingSuccessView.vue  ← Post-payment success page
    │   │   ├── DashboardView.vue   ← Dashboard with storage usage widget
    │   │   └── ...                 ← Other pages (Users, Roles, Orgs, etc.)
    │   ├── components/
    │   │   └── StorageUsageWidget.vue  ← Storage quota progress bar
    │   ├── store/                  ← Vuex state management modules
    │   ├── router/                 ← Vue Router (auth + role guards)
    │   └── api/                    ← Axios API clients
    ├── Dockerfile
    └── nginx.conf                  ← Nginx config (serves Vue + proxies /api/ + /media/)
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
Edit `backend/.env` and fill in your values (see Step 3 above).

### 2. Start everything
```bash
# From the project root
docker compose up --build
```

All 4 services start together:

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

# Run Stripe setup (one-time)
docker compose exec backend python manage.py setup_stripe

# Run migrations manually
docker compose exec backend python manage.py migrate
```

---

## Running Locally (Without Docker)

You need **4 terminals** running simultaneously.

### Terminal 1 — Redis
```bash
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
| Organizations | Multi-tenant orgs — platform admin manages all, org admin manages their own |
| Subscription Plans | Basic / Professional / Premium via Stripe Checkout (monthly or annual) |
| Metered Storage Billing | Per-GB overage charges automatically reported to Stripe |
| Onboarding Flow | 3-step signup form → Stripe payment → org + admin account auto-created |
| Pricing Page | Public pricing page with plan comparison and monthly/annual toggle |
| Roles | Custom roles with assigned permissions per organization |
| Permissions | Fine-grained permission control (role-based + direct user permissions) |
| Users | Invite via email (7-day token), assign roles/permissions, promote/demote |
| My Access | Users can view all their assigned roles and direct permissions |
| Screen Recording | Record screen + mic in-browser via MediaRecorder API |
| File Upload | Upload MP4, WebM, MOV, MKV, MP3, WAV, M4A (up to 500 MB) |
| AI Transcription | Groq Whisper API (free, runs in background via Celery) |
| PDF Export | Professional timestamped transcript PDF (30-second blocks) |
| Storage Tracking | Tracks recording + transcript storage per org, shows usage widget on dashboard |
| Password Reset | OTP via email (15-minute expiry) |
| Rate Limiting | Throttles on login (5/min), password reset (5/hr), invites (20/hr) |

---

## Tech Stack

**Backend**
- Django 4.x + Django REST Framework
- SimpleJWT (JWT authentication with refresh token rotation + blacklisting)
- Celery + Redis (background task processing)
- Stripe SDK v7 (subscription billing + metered storage)
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
- Stripe.js (redirect to hosted checkout)
- Vite (build tool)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy, Vue SPA serving, media file serving)
- Redis (Celery broker + result backend)

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

### Payments & Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/create-checkout-session/` | Create Stripe checkout session |
| POST | `/api/payments/webhook/` | Stripe webhook (payment events) |
| GET | `/api/payments/verify-session/` | Verify payment + create org after checkout |
| GET | `/api/payments/subscription-status/` | Current plan, storage, billing dates |
| GET | `/api/payments/storage-usage/` | Storage breakdown + overage estimate |

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
| `FRONTEND_URL` | No | Used in Stripe redirects and invitation emails (default `http://localhost:8080`) |
| `STRIPE_SECRET_KEY` | Yes | Stripe secret key (test: `sk_test_...`) |
| `STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key (test: `pk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret (for production) |
| `STRIPE_BASIC_MONTHLY_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_BASIC_ANNUAL_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_BASIC_METERED_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PRO_MONTHLY_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PRO_ANNUAL_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PRO_METERED_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PREMIUM_MONTHLY_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PREMIUM_ANNUAL_PRICE_ID` | Yes | Generated by `setup_stripe` command |
| `STRIPE_PREMIUM_METERED_PRICE_ID` | Yes | Generated by `setup_stripe` command |
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
- **Tenant isolation**: every API viewset filters data by the requesting user's role and organization — org admins cannot access other organizations' data
- **Stripe webhook verification**: webhook signature verified in production using `STRIPE_WEBHOOK_SECRET`
- **Pending onboarding expiry**: incomplete onboarding sessions expire after 24 hours
