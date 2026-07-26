# Keystone — Work Outline

This document is the source of truth for build order, file targets, and completion criteria per phase. Update status markers as work progresses.

Status legend: `[ ]` Not started | `[~]` In progress | `[x]` Complete

---

## Automation Architecture — Running Principles

These apply across every phase. Every decision about status modeling, service design, and task structure should be made with this in mind.

- **State machines first** — any entity with a status uses explicit transition definitions, not free-form enum updates. Invalid transitions are rejected at the service layer.
- **Hooks, not hardcoding** — services emit transition events. Automation rules subscribe to those events. No automation logic lives inside service functions directly.
- **Approval queue from day one** — the queue model and dependency exist from Phase 1. Phases 2–6 populate it. Phase 7 activates the UI and rule engine on top of it.
- **A `requires_approval` transition always queues, regardless of `triggered_by`** — manual and automated changes are held to the same standard. A human clicking a button doesn't get to skip the approval step a transition is defined to need; if a transition shouldn't need review when done manually, that's a state-machine design change (make it `requires_approval=False`), not a service-layer bypass.
- **Audit trail always** — every state transition (manual or automated) writes an audit record. Who did it, what changed, what triggered it.
- **Kill switch** — `AUTOMATION_ENABLED` env flag. When false, hooks are registered but never fire. Services and state machines work identically in both modes.

---

## Phase 1 — Scaffold, Auth, Users, Roles & State Machine Foundation

**Goal:** Working FastAPI app with JWT auth, user registration/login, role-based access control, and the foundational infrastructure the automation layer will build on.

### 1.1 Project Scaffold

- [x] Create `app/` package with `__init__.py` in every subpackage
- [x] `app/core/config.py` — Pydantic `Settings` class
  - [x] `DATABASE_URL`
  - [x] `SECRET_KEY`
  - [x] `ALGORITHM`
  - [x] `ACCESS_TOKEN_EXPIRE_MINUTES`
  - [x] `REDIS_URL`
  - [x] Loads from `.env` via `pydantic-settings`
  - [x] `AUTOMATION_ENABLED` bool, default `False`
  - [x] `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- [x] `app/core/database.py`
  - [x] Async engine creation from `DATABASE_URL`
  - [x] `AsyncSessionLocal` factory
  - [x] Declarative `Base`
  - [x] `get_db()` dependency
- [x] `app/core/security.py`
  - [x] `hash_password(password: str) -> str`
  - [x] `verify_password(plain, hashed) -> bool`
  - [x] `create_access_token(data: dict, expires_delta=None) -> str`
  - [x] `decode_access_token(token: str) -> dict | None`
- [x] `app/core/dependencies.py`
  - [x] `get_current_user(token, db)` — decodes JWT, fetches user, 401 if invalid
  - [x] `require_role(*roles)` — dependency factory, 403 if role not in allowed list
  - [x] `get_current_active_user` — 403 if `is_active == False`
  - [x] `get_approval_queue_entry(id, db)` — stub for Phase 7, returns 404 for now
- [x] `app/core/state_machine.py`
  - [x] `Transition` dataclass: `from_state`, `to_state`, `requires_approval: bool`, `automation_hook: str | None`
  - [x] `StateMachine` class: takes entity name + list of `Transition`, exposes `can_transition(from, to) -> bool` and `get_transition(from, to) -> Transition | None`
  - [x] `LISTING_MACHINE` defined (states: `draft`, `active`, `pending`, `under_contract`, `sold`, `off_market`)
  - [x] `PIPELINE_MACHINE` defined (states: `new`, `contacted`, `showing_scheduled`, `offer_submitted`, `negotiating`, `under_contract`, `closed`, `lost`)
  - [x] `DOCUMENT_MACHINE` defined (states: `draft`, `sent`, `signed`, `voided`)
  - [x] `requires_approval` flag set per transition (e.g. `active → under_contract` = True)
- [x] `app/automation/` package stub
  - [x] `__init__.py`
  - [x] `hooks.py` — `register_hook(event: str, fn)` and `fire_hook(event: str, context: dict)` — when `AUTOMATION_ENABLED=False`, `fire_hook` is a no-op
  - [x] `registry.py` — empty dict, hooks registered here in later phases
- [x] `app/models/audit_log.py`
  - [x] `id` UUID PK
  - [x] `entity_type` str (e.g. `listing`, `pipeline`, `document`)
  - [x] `entity_id` UUID
  - [x] `action` str
  - [x] `from_state` nullable str
  - [x] `to_state` nullable str
  - [x] `triggered_by` str (`manual`, `automation`, `system`)
  - [x] `actor_id` FK → `users.id`, nullable
  - [x] `notes` Text, nullable
  - [x] `created_at` timestamp
- [x] `app/models/approval_queue.py`
  - [x] `id` UUID PK
  - [x] `entity_type` str
  - [x] `entity_id` UUID
  - [x] `proposed_action` str
  - [x] `proposed_state` nullable str
  - [x] `context` JSON
  - [x] `status` Enum (`pending`, `approved`, `rejected`, `expired`), default `pending`
  - [x] `created_by` str (`automation`, `system`)
  - [x] `reviewed_by_id` FK → `users.id`, nullable
  - [x] `reviewed_at` timestamp, nullable
  - [x] `expires_at` timestamp, nullable
  - [x] `created_at` timestamp
- [x] `app/main.py`
  - [x] `FastAPI()` instance
  - [x] CORS middleware configured
  - [x] Routers registered (`auth`, `users`)
  - [x] `/health` endpoint returns 200
- [x] `requirements.txt` pinned
- [x] `.env.example` with all required keys
- [x] `alembic init alembic` run, `env.py` wired to async engine + `Base.metadata`
- [x] Initial Alembic migration covering `users`, `audit_log`, `approval_queue`

### 1.2 Users Model & Schema

- [x] `app/models/user.py`
  - [x] `id` UUID PK, default `uuid4`
  - [x] `email` unique, indexed, not null
  - [x] `hashed_password` not null
  - [x] `full_name`
  - [x] `role` Enum (`admin`, `agent`, `buyer`, `seller`), default `buyer`
  - [x] `is_active` bool, default `True`
  - [x] `created_at`, `updated_at` via `TimestampMixin`
- [x] `app/schemas/user.py`
  - [x] `UserCreate`, `UserLogin`, `UserRead`, `UserUpdate`, `Token`
- [x] `app/models/mixins.py` — `TimestampMixin` with `created_at`, `updated_at`

### 1.3 Services & Routes

- [x] `app/services/user.py`
  - [x] `create_user`, `authenticate_user`, `get_user_by_id`, `get_user_by_email`, `update_user`, `deactivate_user`
  - [x] Each mutating function writes to `audit_log`
- [x] `app/routers/auth.py` — `POST /auth/register`, `POST /auth/login`
- [x] `app/routers/users.py` — `GET /users/me`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}`

### 1.4 Tests

- [x] `tests/conftest.py` — async engine fixture, `db_session`, `client`, `create_user_in_db`, `auth_headers(role)`
- [x] `tests/test_auth.py` — register, login, duplicate email, bad credentials, token rejection
- [x] `tests/test_users.py` — profile, role enforcement, self-edit, admin-only delete
- [x] `tests/test_state_machine.py`
  - [x] Valid transition returns `True`
  - [x] Invalid transition returns `False`
  - [x] `requires_approval` flag correct per transition
  - [x] `automation_hook` name returned correctly
- [x] `tests/test_audit_log.py`
  - [x] Audit record written on user creation
  - [x] Audit record includes correct `actor_id`, `entity_type`, `action`

### Phase 1 Completion Criteria

- [x] App starts cleanly with `uvicorn app.main:app --reload`
- [x] Full auth flow works end-to-end
- [x] Role enforcement verified
- [x] State machine correctly validates and rejects transitions for all three entity types
- [x] Audit log and approval queue tables exist and are writable
- [x] `fire_hook` is a confirmed no-op when `AUTOMATION_ENABLED=False`
- [x] `pytest tests/` — all green

---

## Phase 2 — Listings + Status History + Transition Hooks

**Goal:** Full listing CRUD with status tracking via state machine, history log, and automation hooks wired to every transition.

### 2.1 Models

- [x] `app/models/listing.py`
  - [x] Standard fields: `id`, `agent_id`, `seller_id`, `address`, `city`, `state`, `zip`, `price`, `bedrooms`, `bathrooms`, `sqft`, `description`, `mls_id`
  - [x] `status` — transitions enforced via `LISTING_MACHINE`, not raw enum writes
  - [x] `created_at`, `updated_at`
  - [x] Relationship to `ListingStatusHistory` (cascade delete)
- [x] `app/models/listing_status_history.py`
  - [x] `id`, `listing_id`, `previous_status`, `new_status`, `changed_by_id`, `note`, `changed_at`
  - [x] `triggered_by` str — `manual` or `automation`
- [x] Alembic migration for both tables

### 2.2 Schemas

- [x] `ListingCreate`, `ListingRead` (includes `price_per_sqft`), `ListingUpdate`, `ListingStatusUpdate` (new_status, note), `ListingStatusHistoryRead`, `ListingFilterParams`

### 2.3 Service & Routes

- [x] `app/services/listing.py`
  - [x] `create_listing`, `get_listing`, `list_listings`, `update_listing`, `archive_listing`
  - [x] `change_status(db, id, new_status, note, changed_by_id, triggered_by="manual")`
    - [x] Validates transition via `LISTING_MACHINE.can_transition()`
    - [x] If `requires_approval=True` → write to `approval_queue` instead of applying
    - [x] On apply: write `ListingStatusHistory`, write `audit_log`, call `fire_hook(f"listing.{new_status}", context)`
  - [x] `get_status_history`
- [x] `app/routers/listings.py` — all CRUD routes + `PATCH /{id}/status` + `GET /{id}/history`

### 2.4 Automation Hooks (stub registration)

- [x] `app/automation/registry.py` — register stub hooks for:
  - [x] `listing.active` — placeholder for "notify seller listing is live"
  - [x] `listing.under_contract` — placeholder for "generate disclosure doc"
  - [x] `listing.sold` — placeholder for "generate closing summary"
- [x] Hooks log intent to console when `AUTOMATION_ENABLED=False`, fire task when `True`

### 2.5 Tests

- [x] `tests/test_listings.py` — full CRUD, filter, status change, history log
- [x] `tests/test_listing_hooks.py`
  - [x] Status change calls `fire_hook` with correct event name and context
  - [x] When `AUTOMATION_ENABLED=False`, hook fires but is no-op (no side effects)
  - [x] Approval-required transitions write to `approval_queue`, not `listing_status_history`

### Phase 2 Completion Criteria

- [x] Listings CRUD fully functional
- [x] Every status change goes through `LISTING_MACHINE` — invalid transitions rejected with 422
- [x] Approval-required transitions land in queue regardless of `triggered_by`, not applied directly
- [x] Hooks called on every valid transition
- [x] `pytest tests/test_listings.py tests/test_listing_hooks.py -v` — all green

---

## Phase 3 — Contacts & CRM Pipeline + Stage Automation Hooks

**Goal:** Contact management with a deal pipeline governed by `PIPELINE_MACHINE`, automation hooks on stage transitions, and stale deal detection.

### 3.1 Models

- [x] `app/models/contact.py` — `id`, `agent_id`, `user_id`, `full_name`, `email`, `phone`, `type`, `source`, `notes`, timestamps
- [x] `app/models/pipeline.py`
  - [x] `id`, `listing_id`, `contact_id`, `agent_id`, `stage`, `offer_price`, `next_action`, `next_action_date`, `notes`, timestamps
  - [x] `last_stage_change_at` timestamp — used for stale detection
  - [x] Unique constraint: `(listing_id, contact_id)`
- [x] Alembic migration for both tables

### 3.2 Schemas

- [x] `ContactCreate`, `ContactRead`, `ContactUpdate`
- [x] `PipelineCreate`, `PipelineRead`, `PipelineUpdate`, `PipelineFilterParams`

### 3.3 Services & Routes

- [x] `app/services/contact.py` — standard CRUD with ownership checks; `create_contact` fires `contact.created` hook
- [x] `app/services/pipeline.py`
  - [x] `add_to_pipeline`, `get_pipeline_entry`, `list_pipeline`, `remove_pipeline_entry`
  - [x] `update_pipeline_entry(db, id, payload, triggered_by="manual")`
    - [x] Stage change validated via `PIPELINE_MACHINE.get_transition()`
    - [x] On valid transition: update `last_stage_change_at`, write audit log, call `fire_hook(transition.automation_hook, context)`
    - [x] Approval-required transitions → write to `approval_queue`, regardless of `triggered_by` (consistent with updated Phase 2 behavior)
  - [x] `get_stale_pipeline_entries(db, days_threshold)` — entries where `last_stage_change_at` is older than threshold
- [x] `app/routers/contacts.py`, `app/routers/pipeline.py` — standard CRUD
  - [x] `app/routers/pipeline.py` missing `GET /` list route (service has `list_pipeline`, router doesn't expose it yet)
  - [x] `app/routers/contacts.py` has known bugs (missing path params, duplicate `PATCH ""` route for update vs. archive) — needs a pass

### 3.4 Automation Hooks (stub registration)

- [x] `pipeline.offer_submitted` — placeholder "notify agent of new offer"
- [x] `pipeline.closed` — placeholder "generate closing docs, notify all parties"
- [x] `pipeline.lost` — placeholder "trigger re-engagement sequence"
- [x] `contact.created` — placeholder "notify agent of new contact assignment"
- [x] Celery task stub: `tasks/pipeline_tasks.py` — `check_stale_pipeline` periodic task (no-op body, Celery beat schedule defined)

### 3.5 Tests

- [x] `tests/test_contacts.py` — CRUD, ownership, type filter
- [x] `tests/test_pipeline.py` — add, duplicate rejection, stage transitions, filter
- [x] `tests/test_pipeline_hooks.py`
  - [x] `offer_submitted` transition fires correct hook
  - [x] `closed` transition fires correct hook
  - [x] Stale detection returns correct entries given seeded `last_stage_change_at` values
  - [x] Approval-required transitions land in queue (both `manual` and `automation` triggered)

### Phase 3 Completion Criteria

- [x] Contact CRUD with agent ownership enforced
- [x] Pipeline stages advance through `PIPELINE_MACHINE` only
- [x] Stale detection query works correctly
- [x] Hooks fire on every stage transition
- [x] `pytest tests/test_contacts.py tests/test_pipeline.py tests/test_pipeline_hooks.py -v` — all green

---

## Phase 4 — Document Generation + Auto-Generate on Pipeline Stage

**Goal:** PDF generation from Jinja2 templates, documents queued automatically when pipeline hits the right stage, status managed via `DOCUMENT_MACHINE`.

### 4.1 Models & Templates

- [x] `app/models/document.py`
  - [x] `id`, `listing_id`, `contact_id`, `pipeline_id`, `created_by_id`, `type`, `status`, `file_path`, timestamps
  - [x] `generated_by` str — `manual` or `automation`
- [x] Alembic migration
- [x] `app/templates/offer_letter.html`, `listing_agreement.html`, `buyer_rep_agreement.html`, `closing_summary.html`

### 4.2 Schemas

- [x] `DocumentGenerateRequest`, `DocumentRead`, `DocumentStatusUpdate`

### 4.3 Service & Routes

- [x] `app/services/document.py`
  - [x] `render_template`, `generate_pdf`, `save_pdf_to_disk`, `create_document_record`
  - [x] `get_document`, `list_documents`
  - [x] `update_status(db, id, new_status, triggered_by="manual")`
    - [x] Validates via `DOCUMENT_MACHINE.can_transition()`
    - [x] On `sent`: fires `document.sent` hook
    - [x] On `signed`: fires `document.signed` hook
    - [x] Writes audit log on every transition
- [x] `app/routers/documents.py` — generate, list, get, download, status update, void

### 4.4 Automation Hooks

- [x] `_generate_and_queue_document` — shared implementation for automation hooks
- [x] Register hook on `pipeline.offer_submitted` → auto-generate `offer_letter`, write to `approval_queue` for agent review before sending
- [x] Register hook on `listing.active` → auto-generate `listing_agreement`, queue for review
- [x] Register hook on `pipeline.closed` → auto-generate closing summary, queue for review
- [x] `document.sent` hook → placeholder for notification task

### 4.5 Tests

- [x] `tests/test_documents.py` — PDF generation, download, status transitions, auth
- [x] `tests/test_document_hooks.py`
  - [x] `pipeline.offer_submitted` event triggers document auto-generation
  - [x] Generated document lands in `approval_queue` before being marked `sent`
  - [x] Agent approval of queue entry transitions document to `sent`
  - [x] `listing.active` event triggers `listing_agreement` generation

### Phase 4 Completion Criteria

- [x] PDF generates from all three template types
- [x] Auto-generation fires on correct pipeline/listing events
- [x] Generated docs require agent approval before delivery
- [x] `DOCUMENT_MACHINE` enforces valid transitions
- [x] `pytest tests/test_documents.py tests/test_document_hooks.py -v` — all green

---

## Phase 5 — Market Analysis + Analytics-Driven Automation Triggers

**Goal:** Reporting on comps, price/sqft, and days-on-market — plus analytics results feeding back into automation (stale listing flags, pricing alerts).

### 5.1 Service Logic

- [x] `app/services/analytics.py`
  - [x] `get_comps(db, zip, city, min_price, max_price)`
  - [x] `get_price_per_sqft(db, zip=None, city=None)` — guards `sqft == 0`
  - [x] `get_days_on_market(db, zip=None, city=None)` — `sold` listings only, uses status history timestamps
  - [x] `get_agent_summary(db, agent_id)` — counts + avg price
  - [x] `get_listing_report(db, listing_id)` — price, comps, DOM combined
  - [x] `flag_stale_listings(db, days_threshold)` — returns listings in `active` with no status change beyond threshold; fires `listing.stale` hook per result
  - [x] `flag_price_outliers(db, zip, threshold_pct)` — listings priced X% above/below area avg; fires `listing.price_alert` hook per result

### 5.2 Routes

- [x] `GET /analytics/comps`, `/price-per-sqft`, `/days-on-market`, `/agent/{id}/summary`, `/listings/{id}/report`

### 5.3 Automation Hooks

- [x] Register `listing.stale` hook → write to `approval_queue`: "Consider reducing price or archiving"
- [x] Register `listing.price_alert` hook → write to `approval_queue`: "Listing price may need review"
- [x] Celery periodic task: `run_stale_listing_check` — runs `flag_stale_listings` on a schedule

### 5.4 Tests

- [x] `tests/test_analytics.py` — comps, price/sqft, DOM, agent summary, edge cases
- [x] `tests/test_analytics_hooks.py`
  - [x] `flag_stale_listings` fires `listing.stale` hook for qualifying listings only
  - [x] `flag_price_outliers` fires `listing.price_alert` for outliers only
  - [x] Approval queue entries created for each flagged listing

### Phase 5 Completion Criteria

- [x] All analytics queries correct on seeded data
- [x] Stale and price alert detection produces correct queue entries
- [x] Celery beat task registered and runnable
- [x] `pytest tests/test_analytics.py tests/test_analytics_hooks.py -v` — all green

---

## Phase 6 — Notifications as Automation Byproduct

**Goal:** Email (and SMS stub) notifications triggered entirely through the hook system — not standalone manual sends.

### 6.1 Infrastructure

- [x] `app/core/celery_app.py` — Celery configured with Redis broker + backend, autodiscover for `email_tasks`/`sms_tasks`, `async_task` decorator for sync/async bridging
- [x] `app/core/notifications.py` — send_email/Jinja2/_render_template implemented, contract confirmed against email_tasks.py (all four contexts now include `template` key)
  - [x] `app/templates/emails/listing_status.html`
  - [x] `app/templates/emails/document_ready.html`
  - [x] `app/templates/emails/pipeline_stage.html`
  - [x] `app/templates/emails/new_contact.html`
- [x] `app/tasks/email_tasks.py` — one Celery task per notification type, each reads entity from DB to build context
  - [x] `send_listing_status_email(listing_id, recipient_role)` — resolves recipient from `agent`/`seller`
  - [x] `send_document_ready_email(document_id)` — sends to `document.contact`
  - [x] `send_pipeline_stage_email(pipeline_id, recipient_role)` — resolves recipient from `agent`/`contact`
  - [x] `send_new_contact_email(contact_id)` — sends to `contact.agent`
  - [x] Verify actual relationship names (`listing.agent`, `pipeline.contact`, `document.contact`, `contact.agent`) against real models — written on assumption, not yet confirmed against model definitions
- [x] `app/tasks/sms_tasks.py` — stub tasks, same shape as email tasks (no send logic yet)

### 6.2 Hook Registration

Design decision: **one task call per recipient**, not one task looping internally — matches thin-hook architecture and isolates per-recipient send failures. Hooks loop through relevant roles and `.delay()` the task once per role.

- [x] `app/automation/notification_hooks.py` scaffolded — all 8 hook functions registered against `register_hook`, function bodies still `pass`
- [x] `on_listing_active` → loop `["agent", "seller"]`, call `send_listing_status_email.delay(listing_id, role)`
- [x] `on_listing_under_contract` → loop `["agent", "buyer", "seller"]`
- [x] `on_listing_sold` → loop `["agent", "buyer", "seller"]`
- [x] `on_listing_stale` → single call, `recipient_role="agent"`
- [x] `on_pipeline_offer_submitted` → loop `["agent", "contact"]`
- [x] `on_pipeline_closed` → loop `["agent", "contact"]`
- [x] `on_document_sent` → single call to `send_document_ready_email(document_id)` (no `recipient_role` param — always contact)
- [x] `on_contact_created` → single call to `send_new_contact_email(contact_id)`

### 6.3 Idempotency & Reliability

- [x] Dedup key per task: `event_type + entity_id + target_state`
- [x] Celery retry with exponential backoff, max 3 retries
- [x] Failures logged to `audit_log` with `action="notification_failed"`

### 6.4 Tests

- [x] `tests/test_notifications.py`
  - [x] Each hook fires the correct Celery task (eager mode, mock SMTP)
  - [x] Correct recipients per event
  - [x] Idempotency: running same task twice sends only one email
  - [x] Retry on SMTP failure, succeeds on second attempt
  - [x] Failure writes audit log entry

### Phase 6 Completion Criteria

- [x] All notification types fire correctly through hooks
- [x] Zero manual `send_email` calls in service layer — all via hooks
- [x] Tasks idempotent and retriable
- [x] `pytest tests/test_notifications.py -v` — all green

---

## Phase 6.5 — Pre-Engine Security & Hardening Pass

**Goal:** Close out gaps before `AUTOMATION_ENABLED` can be flipped on for real. Phase 7 lets the system take unattended action on live deals — anything shaky in auth, input handling, or notification delivery becomes higher-stakes once the engine is live, even with the approval queue in place. This phase is deliberately inserted before Phase 7 rather than after.

### 6.5.1 Auth Hardening

- [x] Confirmed `.env` is gitignored, not committed — only `.env.example` tracked
- [x] Rate limiting on `POST /auth/login` and `POST /auth/register` (e.g. `slowapi`, ~5/minute per IP)
- [x] Generic error message on failed login — `"Invalid email or password"` instead of `"User not found"`, to avoid leaking whether an email is registered (user enumeration)
- [x] Review JWT expiry (`ACCESS_TOKEN_EXPIRE_MINUTES=60`) and decide if a refresh-token flow is needed before the automation engine may be issuing/relying on longer-lived sessions - no refresh flow for now

### 6.5.2 Input & Rendering Safety

- [x] `app/core/notifications.py` — Jinja2 `Environment` has `autoescape=True` (was missing; user-supplied strings like listing address or contact name could otherwise inject raw HTML into outgoing emails)
- [x] Review free-text fields (`Listings.address`, `Contacts.full_name`, `notes` fields, etc.) for `max_length` constraints in Pydantic schemas — unbounded text feeding into PDFs/emails is a secondary version of the same issue
- [x] Confirm no user-supplied string is interpolated into a SQL query outside the ORM (spot-check any raw SQL, if present)

### 6.5.3 Secrets & Logging

- [x] Confirm SMTP/DB credentials never appear in application logs (check any debug `print`/`echo=True` settings before shipping)
- [ ] Confirm prod deployment does not reuse dev `.env` values (`SECRET_KEY`, `SMTP_PASS`) verbatim — deferred to actual deployment time, not yet applicable while still in dev

### 6.5.4 Tests

- [x] `tests/test_auth.py` — add case: repeated failed logins get rate-limited (429)
- [x] `tests/test_auth.py` — add case: login failure message identical for bad email vs. bad password

### Phase 6.5 Completion Criteria

- [x] Auth endpoints rate-limited and enumeration-resistant
- [x] All Jinja2 rendering paths confirmed autoescaped
- [x] No secrets in logs or committed files
- [x] Sign-off before flipping `AUTOMATION_ENABLED=true` in any shared environment

---

## Phase 7 — Automation Engine + Approval Queue + Override Logs

**Goal:** Activate the automation layer built across all prior phases. Rule engine, approval queue UI endpoints, override tracking, and admin controls.

### 7.1 Rule Engine

- [x] `app/automation/engine.py`
  - [x] `AutomationRule` model: `id`, `name`, `trigger_event`, `condition` (JSON), `action`, `requires_approval`, `is_active`, `created_by_id`, timestamps
  - [x] `evaluate_rules(event, context, db)` — loads active rules for event, evaluates conditions, fires actions or queues approvals
  - [x] `evaluate_condition(condition: dict, context: dict) -> bool` — supports basic comparisons: `eq`, `gt`, `lt`, `contains`, `days_since`
- [x] Alembic migration for `automation_rules` table
- [x] `app/automation/hooks.py` updated — `fire_hook` now calls `evaluate_rules` when `AUTOMATION_ENABLED=True`

### 7.2 Approval Queue API

- [ ] `app/routers/approval_queue.py`
  - [ ] `GET /approval-queue/` — agent/admin sees their pending items, filterable by `entity_type`, `status`
  - [ ] `GET /approval-queue/{id}`
  - [ ] `POST /approval-queue/{id}/approve` — applies proposed state change, writes override log
  - [ ] `POST /approval-queue/{id}/reject` — marks rejected, writes override log
  - [ ] `POST /approval-queue/{id}/modify` — agent edits proposed action before approving
- [ ] `app/services/approval.py`
  - [ ] `get_pending_for_agent(db, agent_id)`
  - [ ] `approve_entry(db, id, reviewer_id)` — applies the queued action, triggers downstream hooks
  - [ ] `reject_entry(db, id, reviewer_id, reason)`
  - [ ] `modify_and_approve(db, id, reviewer_id, modified_context)`
  - [ ] `expire_stale_entries(db)` — marks `pending` entries past `expires_at` as `expired`; Celery periodic task

### 7.3 Override Log

- [ ] `app/models/override_log.py`
  - [ ] `id`, `approval_queue_id`, `reviewer_id`, `action` (`approved`, `rejected`, `modified`), `original_context`, `final_context`, `reason`, `created_at`
- [ ] Alembic migration
- [ ] Every approve/reject/modify writes to `override_log`

### 7.4 Admin Rule Management

- [ ] `app/routers/automation.py` (admin only)
  - [ ] `GET /automation/rules/` — list all rules
  - [ ] `POST /automation/rules/` — create rule
  - [ ] `PATCH /automation/rules/{id}` — update/enable/disable
  - [ ] `DELETE /automation/rules/{id}` — soft delete
  - [ ] `GET /automation/audit-log/` — filterable by entity, date range, triggered_by

### 7.5 Tests

- [ ] `tests/test_automation.py`
  - [ ] Rule evaluates correctly for matching event + context
  - [ ] Rule skipped when condition not met
  - [ ] Approval-required action lands in queue, not applied directly
  - [ ] `approve_entry` applies state change and fires downstream hooks
  - [ ] `reject_entry` marks rejected, no state change applied
  - [ ] `modify_and_approve` applies modified context, not original
  - [ ] Stale entries expired by Celery task
  - [ ] Override log written for every approve/reject/modify
  - [ ] `AUTOMATION_ENABLED=False` — rules loaded but no actions fired
  - [ ] Admin can create/disable rules; non-admin gets 403

### Phase 7 Completion Criteria

- [ ] Rule engine evaluates conditions and fires correct actions
- [ ] Approval queue flow complete: queue → review → approve/reject/modify → apply
- [ ] Override log populated for every human decision
- [ ] `AUTOMATION_ENABLED` kill switch confirmed working
- [ ] Admin rule management endpoints functional
- [ ] `pytest tests/test_automation.py -v` — all green

---

## Cross-Cutting Concerns (apply throughout every phase)

- [ ] All IDs are UUID, generated server-side
- [ ] `created_at` / `updated_at` on every model via `TimestampMixin`
- [ ] Role enforcement via `require_role` dependency — never inline in route handlers
- [ ] Services own all business logic — routers stay thin
- [ ] State machine transition validated at service layer before any DB write
- [ ] Every state transition writes to `audit_log` — manual or automated
- [ ] `fire_hook` called after every successful transition, never before
- [ ] `requires_approval` transitions queue for review regardless of `triggered_by` — consistent across all entity types
- [ ] `AUTOMATION_ENABLED=False` confirmed no-op at hook layer — no side effects
- [ ] Alembic migration committed for every model change
- [ ] No bare `except:` blocks — errors surface as HTTP status codes
- [ ] Consistent error response shape across all routers
- [ ] Every route has at least one happy-path test and one auth/permission-denied test
- [ ] `README.md` phase status updated when any phase marker changes