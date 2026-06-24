# Keystone — Real Estate Management Platform

Keystone is an internal platform built for real estate teams to manage the full transaction lifecycle — from first contact to closed deal. It gives agents a single place to track listings, manage buyer and seller relationships, generate transaction documents, and stay on top of their pipeline — with the system doing the heavy lifting and humans stepping in only when it matters.

The long-term goal is near-full automation: Keystone drives the transaction, agents oversee and override. Every architectural decision is made with that destination in mind.

---

## What Keystone Does

**Listing Management**
Agents create and manage property listings with full status history. Every status transition is governed by a state machine — Active, Under Contract, Pending, Closed — and each change is timestamped, logged, and optionally automated based on pipeline events.

**CRM & Pipeline**
Contacts (buyers, sellers, leads) live in a built-in CRM tied to a deal pipeline. Agents track where every relationship stands, and the system can automatically advance pipeline stages, flag stale deals, and queue next actions based on configurable rules.

**Document Generation**
Common real estate documents — offers, disclosures, listing agreements, buyer rep agreements — are generated automatically at the right pipeline stage, pre-filled from existing data, and queued for agent review before delivery. No manual triggering required.

**Market Analysis & Reporting**
Agents and admins pull market-level reports: average days on market, price trends by area, listing volume over time. Analytics also feed back into the automation layer — stale listings get flagged, underpriced comps surface automatically.

**Automation Engine**
The core of Keystone's long-term vision. A rule-based engine monitors transaction state and triggers actions — document generation, notifications, stage transitions, follow-up scheduling — without agent input. An approval queue surfaces anything that needs a human decision before firing.

**Role-Based Access**
Admins have full access. Agents manage their own book of business. Buyers and sellers each see a focused view — their listings, their documents, their pipeline status — nothing more.

**Notifications**
Automated email and SMS notifications keep all parties informed at key moments: listing status changes, document delivery, pipeline stage advances, and upcoming deadlines. Notifications are a byproduct of the automation engine, not a standalone feature.

---

## Tech Stack

| Layer | Tool |
| --- | --- |
| API | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| PDF Generation | WeasyPrint + Jinja2 |
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
│   │   ├── dependencies.py   # Shared FastAPI deps (auth, roles, approval queue)
│   │   └── state_machine.py  # Transition definitions for listings, pipeline, documents
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic v2 schemas
│   ├── routers/              # FastAPI route handlers (thin — parse, call service, return)
│   ├── services/             # Business logic layer
│   ├── tasks/                # Celery background tasks
│   ├── automation/           # Rule engine, approval queue, trigger registry
│   └── main.py               # App factory + router registration
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── .env
├── .env.example
├── alembic.ini
├── requirements.txt
├── WORK_OUTLINE.md
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

# 6. Start Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./keystone.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=your-mailtrap-user
SMTP_PASS=your-mailtrap-pass
AUTOMATION_ENABLED=false
```

> `AUTOMATION_ENABLED` is a kill switch. When `false`, all automation rules are skipped and the platform operates in fully manual mode. Flip to `true` to activate the rule engine.

---

## Roles

| Role | Access |
| --- | --- |
| `admin` | Full platform access, automation rule management |
| `agent` | Listings, contacts, documents, pipeline, approval queue |
| `buyer` | Own profile, assigned listings, documents |
| `seller` | Own listings, pipeline status, documents |

---

## Automation Overview

Keystone is built toward a model where the system drives transactions and humans oversee. The automation layer is introduced incrementally — infrastructure is laid in early phases so it can be activated in Phase 7 without refactoring.

**Key concepts:**

- **State machines** — every entity with a status (listings, pipeline entries, documents) has explicit valid transitions. Invalid moves are rejected at the service layer.
- **Automation hooks** — each state transition exposes a hook. Rules registered to that hook fire automatically when the transition occurs.
- **Approval queue** — high-stakes automated actions are not fired immediately. They're placed in a queue for agent review. Agents approve, modify, or reject. Anything not acted on within a configurable window can be auto-approved.
- **Audit trail** — every automated action is logged with what triggered it, what it did, and who (if anyone) approved it. Required for compliance.
- **Override log** — every time a human overrides or rejects an automated action, it's recorded. Over time this informs rule refinement.

---

## Build Phases

| Phase | Module | Status |
| --- | --- | --- |
| 1 | Scaffold + Auth + Users/Roles + State Machine Foundation | 🔄 In Progress |
| 2 | Listings + Status History + Transition Hooks | ⬜ Not Started |
| 3 | Contacts & CRM Pipeline + Stage Automation Hooks | ⬜ Not Started |
| 4 | Document Generation + Auto-Generate on Pipeline Stage | ⬜ Not Started |
| 5 | Market Analysis + Analytics-Driven Automation Triggers | ⬜ Not Started |
| 6 | Notifications as Automation Byproduct | ⬜ Not Started |
| 7 | Automation Engine + Approval Queue + Override Logs | ⬜ Not Started |

---

## Testing

```bash
# All tests
pytest tests/ -v

# By phase
pytest tests/test_auth.py tests/test_users.py -v        # Phase 1
pytest tests/test_listings.py -v                         # Phase 2
pytest tests/test_contacts.py tests/test_pipeline.py -v # Phase 3
pytest tests/test_documents.py -v                        # Phase 4
pytest tests/test_analytics.py -v                        # Phase 5
pytest tests/test_notifications.py -v                    # Phase 6
pytest tests/test_automation.py -v                       # Phase 7
```

All tests use an in-memory SQLite database via an async test client. Celery runs in eager mode during tests.

---

## Architecture Notes

- All IDs are UUID, generated server-side
- `created_at` / `updated_at` on every model via shared `TimestampMixin`
- Role enforcement via FastAPI dependency (`require_role`), never inline in route handlers
- Services own all business logic — routers stay thin
- State machines defined centrally in `app/core/state_machine.py` and enforced at the service layer
- Automation hooks are registered against state machine transitions, not hardcoded in services
- Every automated action is written to the audit log before execution
- `AUTOMATION_ENABLED=false` disables all rule engine execution without touching service logic