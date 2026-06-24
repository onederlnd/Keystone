# Keystone — Work Outline

This document is the source of truth for build order, file targets, and completion criteria per phase. Update status markers as work progresses.

Status legend: `[ ]` Not started | `[~]` In progress | `[x]` Complete

---

## Automation Architecture — Running Principles

These apply across every phase. Every decision about status modeling, service design, and task structure should be made with this in mind.

- **State machines first** — any entity with a status uses explicit transition definitions, not free-form enum updates. Invalid transitions are rejected at the service layer.
- **Hooks, not hardcoding** — services emit transition events. Automation rules subscribe to those events. No automation logic lives inside service functions directly.
- **Approval queue from day one** — the queue model and dependency exist from Phase 1. Phases 2–6 populate it. Phase 7 activates the UI and rule engine on top of it.
- **Audit trail always** — every state transition (manual or automated) writes an audit record. Who did it, what changed, what triggered it.
- **Kill switch** — `AUTOMATION_ENABLED` env flag. When false, hooks are registered but never fire. Services and state machines work identically in both modes.

---

## Phase 1 — Scaffold, Auth, Users, Roles & State Machine Foundation

**Goal:** Working FastAPI app with JWT auth, user registration/login, role-based access control, and the foundational infrastructure the automation layer will build on.

### 1.1 Project Scaffold

- [x] Create `app/` package with `__init__.py` in every subpackage
- [~] `app/core/config.py` — Pydantic `Settings` class
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
- [~] `app/core/dependencies.py`
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
- [ ] `app/automation/` package stub
  - [ ] `__init__.py`
  - [ ] `hooks.py` — `register_hook(event: str, fn)` and `fire_hook(event: str, context: dict)` — when `AUTOMATION_ENABLED=False`, `fire_hook` is a no-op
  - [ ] `registry.py` — empty dict, hooks registered here in later phases
- [ ] `app/models/audit_log.py`
  - [ ] `id` UUID PK
  - [ ] `entity_type` str (e.g. `listing`, `pipeline`, `document`)
  - [ ] `entity_id` UUID
  - [ ] `action` str
  - [ ] `from_state` nullable str
  - [ ] `to_state` nullable str
  - [ ] `triggered_by` str (`manual`, `automation`, `system`)
  - [ ] `actor_id` FK → `users.id`, nullable
  - [ ] `notes` Text, nullable
  - [ ] `created_at` timestamp
- [ ] `app/models/approval_queue.py`
  - [ ] `id` UUID PK
  - [ ] `entity_type` str
  - [ ] `entity_id` UUID
  - [ ] `proposed_action` str
  - [ ] `proposed_state` nullable str
  - [ ] `context` JSON
  - [ ] `status` Enum (`pending`, `approved`, `rejected`, `expired`), default `pending`
  - [ ] `created_by` str (`automation`, `system`)
  - [ ] `reviewed_by_id` FK → `users.id`, nullable
  - [ ] `reviewed_at` timestamp, nullable
  - [ ] `expires_at` timestamp, nullable
  - [ ] `created_at` timestamp
- [ ] `app/main.py`
  - [ ] `FastAPI()` instance
  - [ ] CORS middleware configured
  - [ ] Routers registered (`auth`, `users`)
  - [ ] `/health` endpoint returns 200
- [ ] `requirements.txt` pinned
- [ ] `.env.example` with all required keys
- [ ] `alembic init alembic` run, `env.py` wired to async engine + `Base.metadata`
- [ ] Initial Alembic migration covering `users`, `audit_log`, `approval_queue`

### 1.2 User Model & Schema

- [ ] `app/models/user.py`
  - [ ] `id` UUID PK, default `uuid4`
  - [ ] `email` unique, indexed, not null
  - [ ] `hashed_password` not null
  - [ ] `full_name`
  - [ ] `role` Enum (`admin`, `agent`, `buyer`, `seller`), default `buyer`
  - [ ] `is_active` bool, default `True`
  - [ ] `created_at`, `updated_at` via `TimestampMixin`
- [ ] `app/schemas/user.py`
  - [ ] `UserCreate`, `UserLogin`, `UserRead`, `UserUpdate`, `Token`
- [ ] `app/models/mixins.py` — `TimestampMixin` with `created_at`, `updated_at`

### 1.3 Services & Routes

- [ ] `app/services/user_service.py`
  - [ ] `create_user`, `authenticate_user`, `get_user_by_id`, `get_user_by_email`, `update_user`, `deactivate_user`
  - [ ] Each mutating function writes to `audit_log`
- [ ] `app/routers/auth.py` — `POST /auth/register`, `POST /auth/login`
- [ ] `app/routers/users.py` — `GET /users/me`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}`

### 1.4 Tests

- [ ] `tests/conftest.py` — async engine fixture, `db_session`, `client`, `create_user_in_db`, `auth_headers(role)`
- [ ] `tests/test_auth.py` — register, login, duplicate email, bad credentials, token rejection
- [ ] `tests/test_users.py` — profile, role enforcement, self-edit, admin-only delete
- [ ] `tests/test_state_machine.py`
  - [ ] Valid transition returns `True`
  - [ ] Invalid transition returns `False`
  - [ ] `requires_approval` flag correct per transition
  - [ ] `automation_hook` name returned correctly
- [ ] `tests/test_audit_log.py`
  - [ ] Audit record written on user creation
  - [ ] Audit record includes correct `actor_id`, `entity_type`, `action`

### Phase 1 Completion Criteria

- [ ] App starts cleanly with `uvicorn app.main:app --reload`
- [ ] Full auth flow works end-to-end
- [ ] Role enforcement verified
- [ ] State machine correctly validates and rejects transitions for all three entity types
- [ ] Audit log and approval queue tables exist and are writable
- [ ] `fire_hook` is a confirmed no-op when `AUTOMATION_ENABLED=False`
- [ ] `pytest tests/` — all green

---

## Phase 2 — Listings + Status History + Transition Hooks

**Goal:** Full listing CRUD with status tracking via state machine, history log, and automation hooks wired to every transition.

### 2.1 Models

- [ ] `app/models/listing.py`
  - [ ] Standard fields: `id`, `agent_id`, `seller_id`, `address`, `city`, `state`, `zip`, `price`, `bedrooms`, `bathrooms`, `sqft`, `description`, `mls_id`
  - [ ] `status` — transitions enforced via `LISTING_MACHINE`, not raw enum writes
  - [ ] `created_at`, `updated_at`
  - [ ] Relationship to `ListingStatusHistory` (cascade delete)
- [ ] `app/models/listing_status_history.py`
  - [ ] `id`, `listing_id`, `previous_status`, `new_status`, `changed_by_id`, `note`, `changed_at`
  - [ ] `triggered_by` str — `manual` or `automation`
- [ ] Alembic migration for both tables

### 2.2 Schemas

- [ ] `ListingCreate`, `ListingRead` (includes `price_per_sqft`), `ListingUpdate`, `ListingStatusUpdate` (new_status, note), `ListingStatusHistoryRead`, `ListingFilterParams`

### 2.3 Service & Routes

- [ ] `app/services/listing_service.py`
  - [ ] `create_listing`, `get_listing`, `list_listings`, `update_listing`, `archive_listing`
  - [ ] `change_status(db, id, new_status, note, changed_by_id, triggered_by="manual")`
    - [ ] Validates transition via `LISTING_MACHINE.can_transition()`
    - [ ] If `requires_approval=True` and `triggered_by="automation"` → write to `approval_queue` instead of applying
    - [ ] On apply: write `ListingStatusHistory`, write `audit_log`, call `fire_hook(f"listing.{new_status}", context)`
  - [ ] `get_status_history`
- [ ] `app/routers/listings.py` — all CRUD routes + `PATCH /{id}/status` + `GET /{id}/history`

### 2.4 Automation Hooks (stub registration)

- [ ] `app/automation/registry.py` — register stub hooks for:
  - [ ] `listing.active` — placeholder for "notify seller listing is live"
  - [ ] `listing.under_contract` — placeholder for "generate disclosure doc"
  - [ ] `listing.sold` — placeholder for "generate closing summary"
- [ ] Hooks log intent to console when `AUTOMATION_ENABLED=False`, fire task when `True`

### 2.5 Tests

- [ ] `tests/test_listings.py` — full CRUD, filter, status change, history log
- [ ] `tests/test_listing_hooks.py`
  - [ ] Status change calls `fire_hook` with correct event name and context
  - [ ] When `AUTOMATION_ENABLED=False`, hook fires but is no-op (no side effects)
  - [ ] Approval-required transitions write to `approval_queue`, not `listing_status_history`

### Phase 2 Completion Criteria

- [ ] Listings CRUD fully functional
- [ ] Every status change goes through `LISTING_MACHINE` — invalid transitions rejected with 422
- [ ] Approval-required transitions land in queue, not applied directly
- [ ] Hooks called on every valid transition
- [ ] `pytest tests/test_listings.py tests/test_listing_hooks.py -v` — all green

---

## Phase 3 — Contacts & CRM Pipeline + Stage Automation Hooks

**Goal:** Contact management with a deal pipeline governed by `PIPELINE_MACHINE`, automation hooks on stage transitions, and stale deal detection.

### 3.1 Models

- [ ] `app/models/contact.py` — `id`, `agent_id`, `user_id`, `full_name`, `email`, `phone`, `type`, `source`, `notes`, timestamps
- [ ] `app/models/pipeline.py`
  - [ ] `id`, `listing_id`, `contact_id`, `agent_id`, `stage`, `offer_price`, `next_action`, `next_action_date`, `notes`, timestamps
  - [ ] `last_stage_change_at` timestamp — used for stale detection
  - [ ] Unique constraint: `(listing_id, contact_id)`
- [ ] Alembic migration for both tables

### 3.2 Schemas

- [ ] `ContactCreate`, `ContactRead`, `ContactUpdate`
- [ ] `PipelineCreate`, `PipelineRead`, `PipelineUpdate`, `PipelineFilterParams`

### 3.3 Services & Routes

- [ ] `app/services/contact_service.py` — standard CRUD with ownership checks; `create_contact` fires `contact.created` hook
- [ ] `app/services/pipeline_service.py`
  - [ ] `add_to_pipeline`, `get_pipeline_entry`, `list_pipeline`, `remove_pipeline_entry`
  - [ ] `update_pipeline_entry(db, id, payload, triggered_by="manual")`
    - [ ] Stage change validated via `PIPELINE_MACHINE.can_transition()`
    - [ ] On valid transition: update `last_stage_change_at`, write audit log, call `fire_hook(f"pipeline.{new_stage}", context)`
    - [ ] Approval-required transitions → write to `approval_queue`
  - [ ] `get_stale_pipeline_entries(db, days_threshold)` — entries where `last_stage_change_at` is older than threshold
- [ ] `app/routers/contacts.py`, `app/routers/pipeline.py` — standard CRUD

### 3.4 Automation Hooks (stub registration)

- [ ] `pipeline.offer_submitted` — placeholder "notify agent of new offer"
- [ ] `pipeline.closed` — placeholder "generate closing docs, notify all parties"
- [ ] `pipeline.lost` — placeholder "trigger re-engagement sequence"
- [ ] `contact.created` — placeholder "notify agent of new contact assignment"
- [ ] Celery task stub: `tasks/pipeline_tasks.py` — `check_stale_pipeline` periodic task (no-op body, Celery beat schedule defined)

### 3.5 Tests

- [ ] `tests/test_contacts.py` — CRUD, ownership, type filter
- [ ] `tests/test_pipeline.py` — add, duplicate rejection, stage transitions, filter
- [ ] `tests/test_pipeline_hooks.py`
  - [ ] `offer_submitted` transition fires correct hook
  - [ ] `closed` transition fires correct hook
  - [ ] Stale detection returns correct entries given seeded `last_stage_change_at` values
  - [ ] Approval-required transitions land in queue

### Phase 3 Completion Criteria

- [ ] Contact CRUD with agent ownership enforced
- [ ] Pipeline stages advance through `PIPELINE_MACHINE` only
- [ ] Stale detection query works correctly
- [ ] Hooks fire on every stage transition
- [ ] `pytest tests/test_contacts.py tests/test_pipeline.py tests/test_pipeline_hooks.py -v` — all green

---

## Phase 4 — Document Generation + Auto-Generate on Pipeline Stage

**Goal:** PDF generation from Jinja2 templates, documents queued automatically when pipeline hits the right stage, status managed via `DOCUMENT_MACHINE`.

### 4.1 Models & Templates

- [ ] `app/models/document.py`
  - [ ] `id`, `listing_id`, `contact_id`, `pipeline_id`, `created_by_id`, `type`, `status`, `file_path`, timestamps
  - [ ] `generated_by` str — `manual` or `automation`
- [ ] Alembic migration
- [ ] `app/templates/offer_letter.html`, `listing_agreement.html`, `buyer_rep_agreement.html`

### 4.2 Schemas

- [ ] `DocumentGenerateRequest`, `DocumentRead`, `DocumentStatusUpdate`

### 4.3 Service & Routes

- [ ] `app/services/document_service.py`
  - [ ] `render_template`, `generate_pdf`, `save_pdf_to_disk`, `create_document_record`
  - [ ] `get_document`, `list_documents`
  - [ ] `update_status(db, id, new_status, triggered_by="manual")`
    - [ ] Validates via `DOCUMENT_MACHINE.can_transition()`
    - [ ] On `sent`: fires `document.sent` hook
    - [ ] On `signed`: fires `document.signed` hook
    - [ ] Writes audit log on every transition
- [ ] `app/routers/documents.py` — generate, list, get, download, status update, void

### 4.4 Automation Hooks

- [ ] Register hook on `pipeline.offer_submitted` → auto-generate `offer_letter`, write to `approval_queue` for agent review before sending
- [ ] Register hook on `listing.active` → auto-generate `listing_agreement`, queue for review
- [ ] Register hook on `pipeline.closed` → auto-generate closing summary, queue for review
- [ ] `document.sent` hook → placeholder for notification task

### 4.5 Tests

- [ ] `tests/test_documents.py` — PDF generation, download, status transitions, auth
- [ ] `tests/test_document_hooks.py`
  - [ ] `pipeline.offer_submitted` event triggers document auto-generation
  - [ ] Generated document lands in `approval_queue` before being marked `sent`
  - [ ] Agent approval of queue entry transitions document to `sent`
  - [ ] `listing.active` event triggers `listing_agreement` generation

### Phase 4 Completion Criteria

- [ ] PDF generates from all three template types
- [ ] Auto-generation fires on correct pipeline/listing events
- [ ] Generated docs require agent approval before delivery
- [ ] `DOCUMENT_MACHINE` enforces valid transitions
- [ ] `pytest tests/test_documents.py tests/test_document_hooks.py -v` — all green

---

## Phase 5 — Market Analysis + Analytics-Driven Automation Triggers

**Goal:** Reporting on comps, price/sqft, and days-on-market — plus analytics results feeding back into automation (stale listing flags, pricing alerts).

### 5.1 Service Logic

- [ ] `app/services/analytics_service.py`
  - [ ] `get_comps(db, zip, city, min_price, max_price)`
  - [ ] `get_price_per_sqft(db, zip=None, city=None)` — guards `sqft == 0`
  - [ ] `get_days_on_market(db, zip=None, city=None)` — `sold` listings only, uses status history timestamps
  - [ ] `get_agent_summary(db, agent_id)` — counts + avg price
  - [ ] `get_listing_report(db, listing_id)` — price, comps, DOM combined
  - [ ] `flag_stale_listings(db, days_threshold)` — returns listings in `active` with no status change beyond threshold; fires `listing.stale` hook per result
  - [ ] `flag_price_outliers(db, zip, threshold_pct)` — listings priced X% above/below area avg; fires `listing.price_alert` hook per result

### 5.2 Routes

- [ ] `GET /analytics/comps`, `/price-per-sqft`, `/days-on-market`, `/agent/{id}/summary`, `/listings/{id}/report`

### 5.3 Automation Hooks

- [ ] Register `listing.stale` hook → write to `approval_queue`: "Consider reducing price or archiving"
- [ ] Register `listing.price_alert` hook → write to `approval_queue`: "Listing price may need review"
- [ ] Celery periodic task: `run_stale_listing_check` — runs `flag_stale_listings` on a schedule

### 5.4 Tests

- [ ] `tests/test_analytics.py` — comps, price/sqft, DOM, agent summary, edge cases
- [ ] `tests/test_analytics_hooks.py`
  - [ ] `flag_stale_listings` fires `listing.stale` hook for qualifying listings only
  - [ ] `flag_price_outliers` fires `listing.price_alert` for outliers only
  - [ ] Approval queue entries created for each flagged listing

### Phase 5 Completion Criteria

- [ ] All analytics queries correct on seeded data
- [ ] Stale and price alert detection produces correct queue entries
- [ ] Celery beat task registered and runnable
- [ ] `pytest tests/test_analytics.py tests/test_analytics_hooks.py -v` — all green

---

## Phase 6 — Notifications as Automation Byproduct

**Goal:** Email (and SMS stub) notifications triggered entirely through the hook system — not standalone manual sends.

### 6.1 Infrastructure

- [ ] `app/tasks/celery_app.py` — Celery configured with Redis broker + backend
- [ ] `app/core/notifications.py` — `send_email(to, subject, body)` SMTP wrapper + Jinja2 email templates
- [ ] `app/tasks/email_tasks.py` — one Celery task per notification type, each reads entity from DB to build context
- [ ] `app/tasks/sms_tasks.py` — stub tasks, same shape as email tasks

### 6.2 Hook Registration

- [ ] `listing.active` → `send_listing_live_email` (agent + seller)
- [ ] `listing.under_contract` → `send_under_contract_email` (agent + buyer + seller)
- [ ] `listing.sold` → `send_sold_email` (all parties)
- [ ] `listing.stale` → `send_stale_listing_alert_email` (agent only)
- [ ] `pipeline.offer_submitted` → `send_offer_received_email` (agent + seller)
- [ ] `pipeline.closed` → `send_deal_closed_email` (all parties)
- [ ] `document.sent` → `send_document_delivery_email` (contact)
- [ ] `contact.created` → `send_new_contact_email` (agent)

### 6.3 Idempotency & Reliability

- [ ] Dedup key per task: `event_type + entity_id + target_state`
- [ ] Celery retry with exponential backoff, max 3 retries
- [ ] Failures logged to `audit_log` with `action="notification_failed"`

### 6.4 Tests

- [ ] `tests/test_notifications.py`
  - [ ] Each hook fires the correct Celery task (eager mode, mock SMTP)
  - [ ] Correct recipients per event
  - [ ] Idempotency: running same task twice sends only one email
  - [ ] Retry on SMTP failure, succeeds on second attempt
  - [ ] Failure writes audit log entry

### Phase 6 Completion Criteria

- [ ] All notification types fire correctly through hooks
- [ ] Zero manual `send_email` calls in service layer — all via hooks
- [ ] Tasks idempotent and retriable
- [ ] `pytest tests/test_notifications.py -v` — all green

---

## Phase 7 — Automation Engine + Approval Queue + Override Logs

**Goal:** Activate the automation layer built across all prior phases. Rule engine, approval queue UI endpoints, override tracking, and admin controls.

### 7.1 Rule Engine

- [ ] `app/automation/engine.py`
  - [ ] `AutomationRule` model: `id`, `name`, `trigger_event`, `condition` (JSON), `action`, `requires_approval`, `is_active`, `created_by_id`, timestamps
  - [ ] `evaluate_rules(event, context, db)` — loads active rules for event, evaluates conditions, fires actions or queues approvals
  - [ ] `evaluate_condition(condition: dict, context: dict) -> bool` — supports basic comparisons: `eq`, `gt`, `lt`, `contains`, `days_since`
- [ ] Alembic migration for `automation_rules` table
- [ ] `app/automation/hooks.py` updated — `fire_hook` now calls `evaluate_rules` when `AUTOMATION_ENABLED=True`

### 7.2 Approval Queue API

- [ ] `app/routers/approval_queue.py`
  - [ ] `GET /approval-queue/` — agent/admin sees their pending items, filterable by `entity_type`, `status`
  - [ ] `GET /approval-queue/{id}`
  - [ ] `POST /approval-queue/{id}/approve` — applies proposed state change, writes override log
  - [ ] `POST /approval-queue/{id}/reject` — marks rejected, writes override log
  - [ ] `POST /approval-queue/{id}/modify` — agent edits proposed action before approving
- [ ] `app/services/approval_service.py`
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
- [ ] `AUTOMATION_ENABLED=False` confirmed no-op at hook layer — no side effects
- [ ] Alembic migration committed for every model change
- [ ] No bare `except:` blocks — errors surface as HTTP status codes
- [ ] Consistent error response shape across all routers
- [ ] Every route has at least one happy-path test and one auth/permission-denied test
- [ ] `README.md` phase status updated when any phase marker changes