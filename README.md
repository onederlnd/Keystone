# Keystone — Real Estate Management Platform

Keystone is an internal platform built for real estate teams to manage the full transaction lifecycle — from first contact to closed deal. It gives agents a single place to track listings, manage buyer and seller relationships, generate transaction documents, and stay on top of their pipeline — with the system doing the heavy lifting and humans stepping in only when it matters.

The long-term goal is near-full automation: Keystone drives the transaction, agents oversee and override. Every architectural decision is made with that destination in mind.

---

## Where Things Stand

**Phases 1–3 are complete and fully tested.** That means the foundation — auth, roles, listings, contacts, and the deal pipeline — is live and working end-to-end, including the automation scaffolding (state machines, audit logging, and the approval queue) that later phases will build on.

**Not yet built:** document generation, market analytics, notifications, and the automation rule engine itself (Phases 4–7). The infrastructure for all of them already exists in the codebase — hooks, the approval queue, audit logging — so building these phases is additive work, not rework.

| Phase | Module | Status |
| --- | --- | --- |
| 1 | Scaffold + Auth + Users/Roles + State Machine Foundation | ✅ Complete |
| 2 | Listings + Status History + Transition Hooks | ✅ Complete |
| 3 | Contacts & CRM Pipeline + Stage Automation Hooks | ✅ Complete |
| 4 | Document Generation + Auto-Generate on Pipeline Stage | ✅ Complete |
| 5 | Market Analysis + Analytics-Driven Automation Triggers | ✅ Complete |
| 6 | Notifications as Automation Byproduct | ⬜ Not Started |
| 7 | Automation Engine + Approval Queue + Override Logs | ⬜ Not Started |

See `WORK_OUTLINE.md` for the detailed, file-level build checklist behind each phase.

---

## Demo Accounts

Demo accounts (all use password: password123):

| Username | Email |
| --- | --- |
| admin | <admin@keystone.demo> |
| agent | <agent1@keystone.demo> |
| agent | <agent2@keystone.demo> |
| seller | <seller1@keystone.demo> |
| seller | <seller2@keystone.demo> |
| buyer | <buyer1@keystone.demo> |
| buyer | <buyer2@keystone.demo> |

## What Keystone Does Today

**Auth & Roles** — JWT-based login, four roles (`admin`, `agent`, `buyer`, `seller`), with role and ownership checks enforced on every protected route.

**Listing Management** — Agents create and manage property listings with full status history. Every status change (Active, Pending, Under Contract, Sold, Off Market) goes through a state machine that rejects invalid transitions outright. Each change is timestamped and logged, and higher-stakes transitions (e.g. moving to Under Contract) are held for agent approval rather than applied automatically.

**CRM & Pipeline** — Contacts (buyers, sellers, leads) live in a built-in CRM tied to a deal pipeline, scoped so agents only see their own book of business (admins see everything). Pipeline stages — New, Contacted, Showing Scheduled, Offer Submitted, Negotiating, Under Contract, Closed, Lost — follow the same state-machine-and-approval pattern as listings. Stale deals (no stage movement in N days) can be surfaced on a schedule.

## What's Coming Next (Phases 4–7)

**Document Generation** — Offers, disclosures, listing agreements, and buyer rep agreements generated automatically at the right pipeline stage, pre-filled from existing data, and queued for agent review before delivery.

**Market Analysis & Reporting** — Comps, days-on-market, price-per-sqft, and agent performance summaries. Analytics will also feed back into automation — stale listings and mispriced comps flagged automatically.

**Automation Engine** — The core of Keystone's long-term vision. A rule-based engine will monitor transaction state and trigger actions — document generation, notifications, stage transitions — without agent input. Anything with real stakes routes through the approval queue for a human decision first.

**Notifications** — Automated email (and SMS) at key moments: listing status changes, document delivery, pipeline advances. These will be a byproduct of the automation engine firing, not a separate feature to build and maintain.

---

## How the Automation Model Works

This is the architectural backbone that every phase builds on, so it's worth understanding even if you're not writing code:

- **State machines** — every entity with a status (listings, pipeline entries, documents) has an explicit list of valid transitions. You can't move a listing from "Draft" straight to "Sold" — the system won't allow it.
- **Hooks, not hardcoding** — when a valid transition happens, the system emits an event (e.g. `listing.active`). Automation rules subscribe to these events rather than being wired directly into business logic — this is what lets Phase 7's rule engine slot in later without rewriting Phases 2–6.
- **Approval queue** — some transitions are flagged as requiring human review regardless of who or what initiated them. Instead of applying immediately, they're written to a queue for an agent to approve, modify, or reject. This applies uniformly — a human clicking a button doesn't skip the same review an automated action would need.
- **Audit trail** — every transition, manual or automated, is logged: what changed, who or what triggered it, and when.
- **Kill switch** — a single `AUTOMATION_ENABLED` flag. When off, hooks are still registered but never fire — the platform runs in fully manual mode with zero behavior change to the rest of the system. This is what makes it safe to build and test the automation layer incrementally without risking the live manual workflow.

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

> `AUTOMATION_ENABLED` is a kill switch. When `false`, all automation rules are skipped and the platform operates in fully manual mode. Flip to `true` to activate the rule engine (Phase 7).

---

## Roles

| Role | Access |
| --- | --- |
| `admin` | Full platform access, bypasses ownership checks on contacts/listings, automation rule management |
| `agent` | Own listings, contacts, documents, pipeline, approval queue |
| `buyer` | Own profile, assigned listings, documents |
| `seller` | Own listings, pipeline status, documents |

---

## Testing

```bash
# All tests
pytest tests/ -v

# By phase
pytest tests/test_auth.py tests/test_users.py -v                          # Phase 1
pytest tests/test_listings.py tests/test_listing_hooks.py -v              # Phase 2
pytest tests/test_contacts.py tests/test_pipeline.py tests/test_pipeline_hooks.py -v  # Phase 3
pytest tests/test_documents.py -v                                         # Phase 4
pytest tests/test_analytics.py -v                                         # Phase 5
pytest tests/test_notifications.py -v                                     # Phase 6 (pending)
pytest tests/test_automation.py -v                                        # Phase 7 (pending)
```

All tests run against an in-memory SQLite database via an async test client. Celery runs in eager mode during tests.

---

## Architecture Notes (for contributors)

- All IDs are UUID, generated server-side.
- `created_at` / `updated_at` on every model via a shared `TimestampMixin`.
- Role enforcement happens via a FastAPI dependency (`require_role` / `get_current_active_user`), never inline in route handlers.
- Services own all business logic — routers stay thin (parse request, call service, return).
- State machines are defined centrally in `app/core/state_machine.py` and enforced at the service layer, not in routers or models.
- Automation hooks are registered against state machine transitions, not hardcoded inside service functions.
- fire_hook supports async hook functions (inspect.iscoroutinefunction check (import inspect))
- A transition marked `requires_approval` always queues for review, regardless of whether it was triggered manually or by automation — this is intentional and consistent across listings and pipeline.
- Every state transition is written to the audit log before (or as part of) execution.
- `AUTOMATION_ENABLED=false` disables all rule engine execution without touching service logic or requiring code changes elsewhere.
- See `WORK_OUTLINE.md` for the authoritative, up-to-date build checklist — it tracks status at the file and function level and is the source of truth when this README and the code disagree.
