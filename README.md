# Keystone — Real Estate Management Platform

Keystone is an internal real estate management platform built for agents, buyers, and sellers. It automates the full transaction lifecycle: property listings, CRM pipeline, document generation, market analysis, and notifications — all behind a clean FastAPI backend.

---

## Tech Stack

| Layer | Tool |
| --- | --- |
| API | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| PDF Generation | WeasyPrint |
| Background Tasks | Celery + Redis |
| Auth | JWT via `python-jose` + `passlib` |
| Testing | pytest + pytest-asyncio + httpx |
| Config | Pydantic Settings (`.env`) |

---

## Project Structure

```bash
backend/
├── alembic/                  # Migration files
├── app/
│   ├── core/
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Async engine + session
│   │   ├── security.py       # JWT, password hashing
│   │   └── dependencies.py   # Shared FastAPI deps
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic v2 schemas
│   ├── routers/              # FastAPI route handlers
│   ├── services/             # Business logic layer
│   ├── tasks/                # Celery background tasks
│   └── main.py               # App factory + router registration
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── .env
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Create and activate virtualenv
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload
```

---

## Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./keystone.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://localhost:6379/0
```

---

## Roles

| Role | Access |
| --- | --- |
| `admin` | Full platform access |
| `agent` | Listings, contacts, documents, pipeline |
| `buyer` | Own profile, assigned listings, documents |
| `seller` | Own listings, pipeline status, documents |

---

## Phases

See `WORK_OUTLINE.md` for the full phased build plan.

| Phase | Module | Status |
| --- | --- | --- |
| 1 | Project scaffold + Auth + Users/Roles | ⬜ Not started |
| 2 | Listings + Status History | ⬜ Not started |
| 3 | Contacts & CRM Pipeline | ⬜ Not started |
| 4 | Document Generation | ⬜ Not started |
| 5 | Market Analysis & Reporting | ⬜ Not started |
| 6 | Notifications (Email/SMS) | ⬜ Not started |

---

## Testing

```bash
pytest tests/ -v
```

All routes have corresponding test files. Tests use an in-memory SQLite database via an async test client.

---

## Notes

- All IDs are UUID
- Timestamps (`created_at`, `updated_at`) on every model via a shared `BaseModel`
- Role-based access enforced at the dependency layer, not inside routes
- Document templates stored as Jinja2 HTML → rendered to PDF via WeasyPrint
