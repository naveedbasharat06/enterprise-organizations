# RoleBase Dashboard — Django + Vue.js

A role-based dashboard with three roles: **Super Admin**, **Admin**, and **Member**.

---

## Project Structure

```
project/
├── backend/               ← Django REST API
│   ├── core/              ← Django project config (settings, urls)
│   │   ├── settings.py    ← App config, DB, CORS, REST Framework
│   │   └── urls.py        ← Root URL routing
│   ├── accounts/          ← Main Django app
│   │   ├── models.py      ← User + Organization models
│   │   ├── serializers.py ← DRF serializers (JSON conversion)
│   │   ├── views.py       ← API views + ViewSets
│   │   ├── urls.py        ← API endpoint routing
│   │   ├── permissions.py ← Custom role-based permissions
│   │   └── admin.py       ← Django admin panel config
│   ├── manage.py          ← Django CLI tool
│   ├── seed_data.py       ← Creates demo users/orgs
│   └── requirements.txt   ← Python dependencies
│
└── frontend/
    └── index.html         ← Vue.js 3 app (CDN, no build needed)
```

---

## How to Run

### Backend (Django)

```bash
# 1. Go to backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database migrations
python manage.py migrate

# 6. Create demo data (super admin + orgs + users)
python seed_data.py

# 7. Start the server
python manage.py runserver
# → Running at http://localhost:8000
```

### Frontend (Vue.js)

```bash
# Option A — Python simple server (easiest)
cd frontend
python -m http.server 5173
# Open http://localhost:5173

# Option B — Just open the file
# Double-click frontend/index.html in your file explorer
```

---

## Demo Accounts

| Username      | Password    | Role        | Organization |
|---------------|-------------|-------------|--------------|
| superadmin    | Admin@1234  | Super Admin | —            |
| admin_tech    | Admin@1234  | Admin       | Tech Corp    |
| john_member   | Admin@1234  | Member      | —            |

---

## API Endpoints

| Method | Endpoint                              | Who Can Access       |
|--------|---------------------------------------|----------------------|
| POST   | /api/auth/login/                      | Anyone               |
| POST   | /api/auth/logout/                     | Logged in users      |
| GET    | /api/auth/me/                         | Logged in users      |
| GET    | /api/dashboard/stats/                 | Logged in users      |
| GET    | /api/organizations/                   | Logged in users      |
| POST   | /api/organizations/                   | Super Admin only     |
| PATCH  | /api/organizations/{id}/              | Super Admin only     |
| DELETE | /api/organizations/{id}/              | Super Admin only     |
| POST   | /api/organizations/{id}/enroll/       | Members              |
| POST   | /api/organizations/{id}/leave/        | Members              |
| GET    | /api/users/                           | Admin, Super Admin   |
| POST   | /api/users/                           | Anyone (register)    |
| PATCH  | /api/users/{id}/                      | Self or Admin        |
| DELETE | /api/users/{id}/                      | Super Admin only     |
| POST   | /api/users/{id}/make_admin/           | Super Admin only     |
| POST   | /api/users/{id}/make_member/          | Super Admin only     |

---

## Key Concepts (for your colleague)

### Django Backend

- **models.py** — Defines database tables as Python classes. `User` extends Django's built-in `AbstractUser` and adds a `role` field and a foreign key to `Organization`.
- **serializers.py** — Converts Python objects ↔ JSON. DRF serializers validate incoming data and format outgoing responses.
- **views.py** — Contains the API logic. `ViewSet` handles all CRUD automatically. Custom `@action` decorators add extra endpoints like `/enroll/` or `/make_admin/`.
- **permissions.py** — Custom permission classes that check the user's `role` before allowing access.
- **urls.py** — Maps URL patterns to views. `DefaultRouter` auto-generates URLs for ViewSets.
- **settings.py** — `AUTH_USER_MODEL = 'accounts.User'` tells Django to use our custom User model.

### Vue.js Frontend

- Single-file `index.html` using Vue 3 via CDN — no build step needed.
- Uses `reactive()` and `ref()` for state management.
- Token stored in `localStorage` for session persistence.
- All API calls use `fetch()` with `Authorization: Token <token>` header.
- Modals are controlled by a single `modal` reactive object with `type` and `data`.

---

## Role Permissions Summary

| Feature                    | Member | Admin | Super Admin |
|----------------------------|--------|-------|-------------|
| View organizations         | ✅     | ✅    | ✅          |
| Join / leave organization  | ✅     | ✗     | ✗           |
| Manage organization users  | ✗      | ✅    | ✅          |
| Create organization        | ✗      | ✗     | ✅          |
| Create/delete users        | ✗      | ✗     | ✅          |
| Promote/demote users       | ✗      | ✗     | ✅          |
