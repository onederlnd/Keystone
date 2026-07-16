# Keystone: Real Estate Transaction Platform

## What It Is

Keystone is a platform built for real estate teams to manage a deal from the very first contact with a buyer or seller all the way through closing. Instead of agents juggling spreadsheets, email threads, and paper documents, everything (listings, client relationships, deal progress, and paperwork) lives in one system.

The long-term vision is a platform that **actively drives the transaction forward**, handling routine steps automatically, while agents stay in control and step in for anything that actually needs a human decision.

## What's Working Today

**Logins & Roles**
Four types of users (admins, agents, buyers, and sellers) each see only what's relevant to them. Agents manage their own clients and listings; admins see everything.

**Listings**
Agents create and track property listings through their full lifecycle: Active, Pending, Under Contract, Sold (or Off Market). The system enforces valid next steps, so a listing can't jump straight from "just listed" to "sold," for example, and every change is time-stamped and logged.

**Client Relationship Management (CRM)**
A built-in CRM tracks every buyer, seller, and lead through a deal pipeline (New, Contacted, Showing Scheduled, Offer Submitted, Negotiating, Under Contract, Closed/Lost). Agents only see their own book of business.

**Document Generation**
Offers, disclosures, and agreements are generated automatically at the right point in a deal, pre-filled with existing data, and held for agent review before anything goes out.

**Market Analysis**
Comps, days-on-market, price-per-square-foot, and agent performance reporting, with the numbers feeding back into the system to flag things like stale listings or mispriced comps.

## What's Being Built Next

**Notifications** *(in progress)*
Automatic email and text alerts at key moments: a listing status change, a document ready for signature, a deal moving to the next stage. The email pipeline (Celery tasks, SMTP wrapper, Jinja2 templates) is built; wiring each automation hook to actually fire the right task for the right recipients is the remaining work.

**Pre-Engine Hardening** *(current focus)*
Before the automation engine goes live, this is a pass to close out notifications and shore up security — since Phase 7 is what starts taking real, unattended action on live deals. See "Current Status" below.

**The Automation Engine** *(next up, this is the big one)*
This is what the whole platform has been built toward: a rule-based system that watches deals in progress and takes routine action on its own, generating a document, sending a notification, advancing a stage, without an agent having to trigger it manually.

Anything with real stakes (money, legal documents, a status change a client will see) is never applied automatically. It's queued for an agent to approve, adjust, or reject first. A human clicking "approve" goes through the exact same review step as an automated action would; there's no shortcut that skips oversight.

There's also a single on/off switch for the whole automation layer. With it off, the platform runs in fully manual mode, identical to how it works today, which is what makes it safe to build and test the automation piece without risk to how agents already use the system day-to-day.

## Exploratory — Intelligence Layer

Not yet scoped or scheduled. Captures direction while it's fresh: building a proper ML layer into Keystone (not an LLM — classical/lightweight models: regression, gradient boosted trees, anomaly detection), reusing the two patterns already proven in the platform rather than inventing new ones.

The idea: every model's output becomes an event, same as `listing.stale` today (e.g. `pipeline.risk_elevated`, `listing.price_suggested`). Every suggestion routes through the existing approval queue, so AI-driven suggestions get the same human-in-the-loop guarantee as rule-based automation — no separate "AI path" that bypasses review. Retraining reuses `override_log` (Phase 7) as each model's training signal, since agent approve/dismiss decisions are ground-truth labels no off-the-shelf competitor platform has access to.

Candidate models, split by data readiness:

- **Buildable now** (Phase 1–5 data): comps-based pricing regression, days-on-market prediction, price anomaly detection
- **Needs Phase 7 first** (`override_log` as training data): deal fall-through risk, lead/deal scoring, optimal-listing-price-vs-agent-guess
- **Lower priority / batch**: lead source ROI scoring, comp similarity scoring, emerging neighborhood detection

Revisit once Phase 7 has shipped and produced enough real usage data to train against — building this before Phase 7 means training on incomplete data that gets thrown away almost immediately.

## The Short Version

Keystone today is a solid, fully working CRM and transaction tracker. Agents can already run listings, clients, and paperwork through the system end-to-end instead of piecing it together across spreadsheets and email.

What's coming next is the part that makes it more than just a nicer spreadsheet: a system that does the busywork of a real estate deal automatically (generating documents, sending updates, advancing a deal to its next stage) with a human always making the final call on anything that matters. The goal isn't to remove agents from the process; it's to remove the parts of the process that don't need them.

## Current Status

| Phase | Module | Status |
| --- | --- | --- |
| 1 | Scaffold + Auth + Users/Roles + State Machine Foundation | ✅ Complete |
| 2 | Listings + Status History + Transition Hooks | ✅ Complete |
| 3 | Contacts & CRM Pipeline + Stage Automation Hooks | ✅ Complete |
| 4 | Document Generation + Auto-Generate on Pipeline Stage | ✅ Complete |
| 5 | Market Analysis + Analytics-Driven Automation Triggers | ✅ Complete |
| 6 | Notifications as Automation Byproduct | 🔶 In Progress |
| 6.5 | Pre-Engine Security & Hardening Pass | ⬜ Not Started |
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

## What's Coming Next (Phases 6.5–7)

**Notifications (finishing Phase 6)** — Celery + Redis background tasks, SMTP wrapper, and Jinja2 email templates are built. Remaining: wire each of the 8 automation hooks (`listing.active`, `pipeline.closed`, etc.) to actually dispatch the right email task to the right recipients, plus idempotency/retry handling.

**Security & Hardening (Phase 6.5)** — A deliberate pause before the automation engine goes live, since Phase 7 is what starts taking real, unattended action. Covers auth rate limiting, error message hardening, and a pass over Jinja2/user-input handling. See `WORK_OUTLINE.md` for the itemized checklist.

**Automation Engine (Phase 7)** — The core of Keystone's long-term vision. A rule-based engine will monitor transaction state and trigger actions — document generation, notifications, stage transitions — without agent input. Anything with real stakes routes through the approval queue for a human decision first.

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
| Email | aiosmtplib + Jinja2 templates |
| Auth | JWT via `python-jose` + `passlib` |
| Testing | pytest + pytest-asyncio + httpx |
| Config | Pydantic Settings (`.env`) |

---

## Project Structure

```bash
realestate/
├── alembic/                  # Migration files
├── app/
│   ├── core/
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # Async engine + session
│   │   ├── security.py       # JWT, password hashing
│   │   ├── dependencies.py   # Shared FastAPI deps (auth, roles, approval queue)
│   │   ├── state_machine.py  # Transition definitions for listings, pipeline, documents
│   │   └── notifications.py  # send_email SMTP wrapper + Jinja2 email templates
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic v2 schemas
│   ├── routers/                # FastAPI route handlers (thin — parse, call service, return)
│   ├── services/                # Business logic layer
│   ├── tasks/                    # Celery background tasks (celery_app, email_tasks, sms_tasks)
│   ├── automation/                # Rule engine, approval queue, trigger registry, notification hooks
│   ├── templates/emails/           # Jinja2 email templates
│   └── main.py                       # App factory + router registration
├── scripts/
│   └── seed.py                # Dev database seeding
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── .env
├── .env.example
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── WORK_OUTLINE.md
└── README.md
```

> Note: `app/` was moved to the project root (previously nested under `backend/`) to simplify imports — everything is now `app.x`, not `backend.app.x`.

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

> `.env` is gitignored — only `.env.example` (with placeholder values) is committed.

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

All tests run against an in-memory SQLite database via an async test client. Celery runs in eager mode during tests (`task_eager_mode` fixture in `conftest.py`, reset after each test).

---

## Architecture Notes (for contributors)

- All IDs are UUID, generated server-side.
- `created_at` / `updated_at` on every model via a shared `TimestampMixin`.
- Role enforcement happens via a FastAPI dependency (`require_role` / `get_current_active_user`), never inline in route handlers.
- Services own all business logic — routers stay thin (parse request, call service, return).
- State machines are defined centrally in `app/core/state_machine.py` and enforced at the service layer, not in routers or models.
- Automation hooks are registered against state machine transitions, not hardcoded inside service functions.
- `fire_hook` supports async hook functions (`inspect.iscoroutinefunction` check).
- A transition marked `requires_approval` always queues for review, regardless of whether it was triggered manually or by automation — this is intentional and consistent across listings and pipeline.
- Every state transition is written to the audit log before (or as part of) execution.
- `AUTOMATION_ENABLED=false` disables all rule engine execution without touching service logic or requiring code changes elsewhere.
- Celery tasks are sync functions (`@celery_app.task`) — bodies are `async def` and bridged via the `async_task` decorator in `app/tasks/celery_app.py`, which wraps `asyncio.run(...)` around the coroutine. Do not `@celery_app.task` an `async def` function directly; Celery workers call tasks synchronously and won't await a coroutine on their own.
- Jinja2 email rendering (`app/core/notifications.py`) has `autoescape=True` — required since template context can include user-supplied strings (listing address, contact name).
- See `WORK_OUTLINE.md` for the authoritative, up-to-date build checklist — it tracks status at the file and function level and is the source of truth when this README and the code disagree.