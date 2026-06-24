# Keystone — Work Outline

This document is the source of truth for build order, file targets, and completion criteria per phase. Update status markers as work progresses.

Status legend: `[ ]` Not started | `[~]` In progress | `[x]` Complete

---

## Phase 1 — Scaffold, Auth, Users & Roles

**Goal:** Working FastAPI app with JWT auth, user registration/login, and role-based access control.

### 1.1 Project Scaffold

- [x] Create `app/` package with `__init__.py` in every subpackage
- [ ] `app/core/config.py` — Pydantic `Settings` class
  - [x] `DATABASE_URL`
  - [x] `SECRET_KEY`
  - [x] `ALGORITHM`
  - [x] `ACCESS_TOKEN_EXPIRE_MINUTES`
  - [x] `REDIS_URL`
  - [x] Loads from `.env` via `pydantic-settings`
- [x] `app/core/database.py`
  - [x] Async engine creation from `DATABASE_URL`
  - [x] `AsyncSessionLocal` factory
  - [x] Declarative `Base`
  - [x] `get_db()` dependency (yields session, closes on exit)
- [ ] `app/core/security.py`
  - [ ] `hash_password(password: str) -> str`
  - [ ] `verify_password(plain, hashed) -> bool`
  - [ ] `create_access_token(data: dict, expires_delta=None) -> str`
  - [ ] `decode_access_token(token: str) -> dict | None`
- [ ] `app/core/dependencies.py`
  - [ ] `get_current_user(token, db)` — decodes JWT, fetches user, 401 if invalid
  - [ ] `require_role(*roles)` — dependency factory, 403 if role not in allowed list
  - [ ] `get_current_active_user` — 403 if `is_active == False`
- [ ] `app/main.py`
  - [ ] App factory / `FastAPI()` instance
  - [ ] CORS middleware configured
  - [ ] Routers registered (`auth`, `users`)
  - [ ] `/health` endpoint returns 200
- [ ] `requirements.txt` pinned: fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, pydantic, pydantic-settings, python-jose, passlib[bcrypt], pytest, pytest-asyncio, httpx
- [ ] `.env.example` with all required keys, no real secrets
- [ ] `alembic init alembic` run, `env.py` wired to async engine + `Base.metadata`

### 1.2 User Model & Schema

- [ ] `app/models/user.py`
  - [ ] `id` UUID PK, default `uuid4`
  - [ ] `email` unique, indexed, not null
  - [ ] `hashed_password` not null
  - [ ] `full_name`
  - [ ] `role` Enum (`admin`, `agent`, `buyer`, `seller`), default `buyer`
  - [ ] `is_active` bool, default `True`
  - [ ] `created_at`, `updated_at` (shared `TimestampMixin`)
- [ ] `app/schemas/user.py`
  - [ ] `UserCreate` (email, password, full_name, role)
  - [ ] `UserLogin` (email, password)
  - [ ] `UserRead` (id, email, full_name, role, is_active, created_at) — excludes password
  - [ ] `UserUpdate` (optional fields, partial update)
  - [ ] `Token` (access_token, token_type)
- [ ] First Alembic migration generated and applied (`users` table)

### 1.3 Services & Routes

- [ ] `app/services/user_service.py`
  - [ ] `create_user(db, payload)` — checks email uniqueness, hashes password
  - [ ] `authenticate_user(db, email, password)` — returns user or `None`
  - [ ] `get_user_by_id(db, id)`
  - [ ] `get_user_by_email(db, email)`
  - [ ] `update_user(db, id, payload)`
  - [ ] `deactivate_user(db, id)`
- [ ] `app/routers/auth.py`
  - [ ] `POST /auth/register` → 201 + `UserRead`, 409 on duplicate email
  - [ ] `POST /auth/login` → 200 + `Token`, 401 on bad credentials
- [ ] `app/routers/users.py`
  - [ ] `GET /users/me` → current user profile
  - [ ] `GET /users/{id}` → 403 unless admin/agent
  - [ ] `PATCH /users/{id}` → self or admin only
  - [ ] `DELETE /users/{id}` → admin only, soft-deactivate not hard delete

### 1.4 Tests

- [ ] `tests/conftest.py`
  - [ ] In-memory SQLite async engine fixture
  - [ ] `db_session` fixture with rollback per test
  - [ ] `client` fixture (httpx `AsyncClient`)
  - [ ] `create_user_in_db` helper fixture/factory
  - [ ] `auth_headers(role)` fixture — registers + logs in a user, returns Bearer header
- [ ] `tests/test_auth.py`
  - [ ] Register succeeds with valid payload
  - [ ] Register fails on duplicate email (409)
  - [ ] Register fails on invalid email/short password (422)
  - [ ] Login succeeds with correct credentials
  - [ ] Login fails with wrong password (401)
  - [ ] Login fails with nonexistent email (401)
  - [ ] Protected route rejects missing token (401)
  - [ ] Protected route rejects malformed/expired token (401)
- [ ] `tests/test_users.py`
  - [ ] `GET /users/me` returns correct profile for logged-in user
  - [ ] `GET /users/{id}` succeeds for admin
  - [ ] `GET /users/{id}` succeeds for agent
  - [ ] `GET /users/{id}` returns 403 for buyer/seller
  - [ ] `PATCH /users/{id}` succeeds for self
  - [ ] `PATCH /users/{id}` returns 403 for non-self/non-admin
  - [ ] `DELETE /users/{id}` succeeds for admin, sets `is_active=False`
  - [ ] `DELETE /users/{id}` returns 403 for non-admin

### Phase 1 Completion Criteria

- [ ] App starts cleanly with `uvicorn app.main:app --reload`
- [ ] Full flow works end-to-end: register → login → use JWT on protected route
- [ ] Role enforcement verified (buyer blocked from agent-only routes)
- [ ] `pytest tests/test_auth.py tests/test_users.py -v` — all green

---

## Phase 2 — Listings & Status History

**Goal:** Full property listing CRUD with status tracking and history log.

### 2.1 Models

- [ ] `app/models/listing.py`
  - [ ] `id` UUID PK
  - [ ] `agent_id` FK → `users.id`, not null
  - [ ] `seller_id` FK → `users.id`, not null
  - [ ] `address`, `city`, `state`, `zip` — not null
  - [ ] `price` Decimal(12,2)
  - [ ] `bedrooms`, `bathrooms` (Integer/Float), `sqft` Integer
  - [ ] `description` Text, nullable
  - [ ] `status` Enum (`draft`, `active`, `pending`, `under_contract`, `sold`, `off_market`), default `draft`
  - [ ] `mls_id` nullable, unique if present
  - [ ] `created_at`, `updated_at`
  - [ ] Relationship to `ListingStatusHistory` (cascade delete)
- [ ] `app/models/listing_status_history.py`
  - [ ] `id` UUID PK
  - [ ] `listing_id` FK → `listings.id`, not null
  - [ ] `previous_status`, `new_status`
  - [ ] `changed_by_id` FK → `users.id`
  - [ ] `note` nullable
  - [ ] `changed_at` default now
- [ ] Alembic migration generated and applied for both tables

### 2.2 Schemas

- [ ] `app/schemas/listing.py`
  - [ ] `ListingCreate`
  - [ ] `ListingRead` (includes computed `price_per_sqft`)
  - [ ] `ListingUpdate` (partial)
  - [ ] `ListingStatusUpdate` (new_status, note)
  - [ ] `ListingStatusHistoryRead`
  - [ ] `ListingFilterParams` (status, agent_id, min_price, max_price)

### 2.3 Service & Routes

- [ ] `app/services/listing_service.py`
  - [ ] `create_listing(db, payload, agent_id)`
  - [ ] `get_listing(db, id)` — 404 if missing
  - [ ] `list_listings(db, filters)` — applies status/agent/price filters
  - [ ] `update_listing(db, id, payload)`
  - [ ] `archive_listing(db, id)` — sets status `off_market`, doesn't hard-delete
  - [ ] `change_status(db, id, new_status, note, changed_by_id)` — writes `ListingStatusHistory` row in same transaction
  - [ ] `get_status_history(db, id)`
- [ ] `app/routers/listings.py`
  - [ ] `POST /listings/` — agent only
  - [ ] `GET /listings/` — supports `status`, `agent_id`, `min_price`, `max_price` query params
  - [ ] `GET /listings/{id}`
  - [ ] `PATCH /listings/{id}` — agent who owns it, or admin
  - [ ] `DELETE /listings/{id}` — archive, not hard delete
  - [ ] `PATCH /listings/{id}/status`
  - [ ] `GET /listings/{id}/history`

### 2.4 Tests (`tests/test_listings.py`)

- [ ] Create listing succeeds for agent
- [ ] Create listing fails for buyer/seller (403)
- [ ] List listings returns expected set with no filters
- [ ] Filter by `status` returns correct subset
- [ ] Filter by `agent_id` returns correct subset
- [ ] Filter by price range returns correct subset
- [ ] Get single listing returns 404 for nonexistent id
- [ ] Update listing succeeds for owning agent
- [ ] Update listing fails for non-owning agent (403)
- [ ] Status change writes a `ListingStatusHistory` row with correct before/after
- [ ] Status history endpoint returns rows in chronological order
- [ ] Archive (`DELETE`) sets status instead of removing the row
- [ ] Unauthorized (no token) requests rejected on every write route

### Phase 2 Completion Criteria

- [ ] Listings CRUD fully functional via API
- [ ] Status change always produces exactly one history record
- [ ] All three filters (status, agent_id, price range) work standalone and combined
- [ ] Unauthorized users cannot create/edit/delete listings
- [ ] `pytest tests/test_listings.py -v` — all green

---

## Phase 3 — Contacts & CRM Pipeline

**Goal:** Contact management for buyers/sellers with a deal pipeline per listing.

### 3.1 Models

- [ ] `app/models/contact.py`
  - [ ] `id` UUID PK
  - [ ] `agent_id` FK → `users.id`, not null
  - [ ] `user_id` FK → `users.id`, nullable
  - [ ] `full_name`, `email`, `phone`
  - [ ] `type` Enum (`buyer`, `seller`, `lead`)
  - [ ] `source` (free text or enum)
  - [ ] `notes` Text, nullable
  - [ ] `created_at`, `updated_at`
- [ ] `app/models/pipeline.py`
  - [ ] `id` UUID PK
  - [ ] `listing_id` FK → `listings.id`
  - [ ] `contact_id` FK → `contacts.id`
  - [ ] `agent_id` FK → `users.id`
  - [ ] `stage` Enum (`new`, `contacted`, `showing_scheduled`, `offer_submitted`, `negotiating`, `under_contract`, `closed`, `lost`), default `new`
  - [ ] `offer_price` Decimal, nullable
  - [ ] `next_action` Text, nullable
  - [ ] `next_action_date` Date, nullable
  - [ ] `notes` Text, nullable
  - [ ] `created_at`, `updated_at`
  - [ ] Unique constraint: `(listing_id, contact_id)` — no duplicate pipeline entries
- [ ] Alembic migration for both tables

### 3.2 Schemas

- [ ] `app/schemas/contact.py` — `ContactCreate`, `ContactRead`, `ContactUpdate`
- [ ] `app/schemas/pipeline.py` — `PipelineCreate`, `PipelineRead`, `PipelineUpdate`, `PipelineFilterParams`

### 3.3 Services & Routes

- [ ] `app/services/contact_service.py`
  - [ ] `create_contact(db, payload, agent_id)`
  - [ ] `get_contact(db, id)` — 404 if missing
  - [ ] `list_contacts(db, filters)` — by `type`, `agent_id`
  - [ ] `update_contact(db, id, payload)` — ownership check
  - [ ] `delete_contact(db, id)` — ownership check
- [ ] `app/services/pipeline_service.py`
  - [ ] `add_to_pipeline(db, payload)` — rejects duplicate `(listing_id, contact_id)`
  - [ ] `list_pipeline(db, filters)` — by `agent_id`, `stage`, `listing_id`
  - [ ] `get_pipeline_entry(db, id)`
  - [ ] `update_pipeline_entry(db, id, payload)` — stage transitions validated
  - [ ] `remove_pipeline_entry(db, id)`
- [ ] `app/routers/contacts.py` — all 5 CRUD routes, agent ownership enforced
- [ ] `app/routers/pipeline.py` — all 5 CRUD routes, agent ownership enforced

### 3.4 Tests

- [ ] `tests/test_contacts.py`
  - [ ] Create contact succeeds for agent
  - [ ] List contacts filters by `type`
  - [ ] List contacts filters by `agent_id`
  - [ ] Agent cannot view/edit another agent's contact (403)
  - [ ] Update contact succeeds for owning agent
  - [ ] Delete contact succeeds for owning agent
- [ ] `tests/test_pipeline.py`
  - [ ] Add contact to pipeline succeeds
  - [ ] Duplicate `(listing_id, contact_id)` rejected (409)
  - [ ] List pipeline filters by `agent_id`
  - [ ] List pipeline filters by `stage`
  - [ ] List pipeline filters by `listing_id`
  - [ ] Stage update moves entry from `new` → `contacted` → ... correctly
  - [ ] Update `next_action`/`next_action_date` persists
  - [ ] Remove pipeline entry succeeds for owning agent, 403 otherwise

### Phase 3 Completion Criteria

- [ ] Contact CRUD works with agent ownership enforced
- [ ] Pipeline stages advance correctly and reject duplicates
- [ ] Filtering by stage, agent, and listing all work
- [ ] `pytest tests/test_contacts.py tests/test_pipeline.py -v` — all green

---

## Phase 4 — Document Generation

**Goal:** Generate offer letters, listing agreements, and buyer representation agreements as PDFs using Jinja2 templates + WeasyPrint.

### 4.1 Model & Templates

- [ ] `app/models/document.py`
  - [ ] `id` UUID PK
  - [ ] `listing_id` FK, nullable
  - [ ] `contact_id` FK, nullable
  - [ ] `pipeline_id` FK, nullable
  - [ ] `created_by_id` FK → `users.id`
  - [ ] `type` Enum (`offer_letter`, `listing_agreement`, `buyer_rep`, `other`)
  - [ ] `status` Enum (`draft`, `sent`, `signed`, `voided`), default `draft`
  - [ ] `file_path` Text
  - [ ] `created_at`, `updated_at`
- [ ] Alembic migration for `documents` table
- [ ] `app/templates/offer_letter.html` — Jinja2, includes listing + contact + offer price
- [ ] `app/templates/listing_agreement.html` — Jinja2, includes listing + seller + agent
- [ ] `app/templates/buyer_rep_agreement.html` — Jinja2, includes buyer + agent
- [ ] Confirm WeasyPrint system deps installed (cairo/pango) and documented in README

### 4.2 Schemas

- [ ] `app/schemas/document.py` — `DocumentGenerateRequest` (type, listing_id, contact_id, pipeline_id, extra_context), `DocumentRead`, `DocumentStatusUpdate`

### 4.3 Service & Routes

- [ ] `app/services/document_service.py`
  - [ ] `render_template(type, context)` — picks correct Jinja2 template
  - [ ] `generate_pdf(html_str) -> bytes` via WeasyPrint
  - [ ] `save_pdf_to_disk(bytes, filename) -> path`
  - [ ] `create_document_record(db, ...)`
  - [ ] `get_document(db, id)`
  - [ ] `list_documents(db, filters)`
  - [ ] `update_status(db, id, new_status)` — validates allowed transitions (`draft→sent→signed`, any→`voided`)
- [ ] `app/routers/documents.py`
  - [ ] `POST /documents/generate`
  - [ ] `GET /documents/`
  - [ ] `GET /documents/{id}`
  - [ ] `GET /documents/{id}/download` — `FileResponse`/streaming, correct `Content-Type`
  - [ ] `PATCH /documents/{id}/status`
  - [ ] `DELETE /documents/{id}` — marks `voided`, optionally removes file

### 4.4 Tests (`tests/test_documents.py`)

- [ ] Generate `offer_letter` produces a valid PDF (check file exists + magic bytes `%PDF`)
- [ ] Generate `listing_agreement` produces a valid PDF
- [ ] Generate `buyer_rep` produces a valid PDF
- [ ] Document record created with correct `file_path` and `type`
- [ ] `GET /documents/{id}/download` returns 200 with `application/pdf` content type
- [ ] `GET /documents/{id}/download` returns 404 for missing document
- [ ] Status transition `draft → sent` succeeds
- [ ] Status transition `sent → signed` succeeds
- [ ] Invalid status transition rejected (e.g. `signed → draft`)
- [ ] Unauthorized user cannot generate or download another agent's documents

### Phase 4 Completion Criteria

- [ ] PDF generates from each of the three template types with real data
- [ ] File saved to disk and path stored in DB correctly
- [ ] Download endpoint streams PDF with correct headers
- [ ] Status transitions enforced (draft → sent → signed, any → voided)
- [ ] `pytest tests/test_documents.py -v` — all green

---

## Phase 5 — Market Analysis & Reporting

**Goal:** Basic comps, price-per-sqft analysis, and summary reports per agent or listing.

### 5.1 Service Logic

- [ ] `app/services/analytics_service.py`
  - [ ] `get_comps(db, zip, city, min_price, max_price)` — excludes the subject listing if provided
  - [ ] `get_price_per_sqft(db, zip=None, city=None)` — handles `sqft == 0` safely (skip or guard division)
  - [ ] `get_days_on_market(db, zip=None, city=None)` — only `sold` listings, uses `created_at` → status-change-to-`sold` timestamp from history table
  - [ ] `get_agent_summary(db, agent_id)` — counts of active/pending/closed + avg price
  - [ ] `get_listing_report(db, listing_id)` — combines list price, comps, DOM into one payload

### 5.2 Routes (`app/routers/analytics.py`)

- [ ] `GET /analytics/comps` — query params `zip`, `city`, `min_price`, `max_price`
- [ ] `GET /analytics/price-per-sqft` — query params `zip` or `city`
- [ ] `GET /analytics/days-on-market` — query params `zip` or `city`
- [ ] `GET /analytics/agent/{id}/summary`
- [ ] `GET /analytics/listings/{id}/report`

### 5.3 Tests (`tests/test_analytics.py`)

- [ ] Comps returns only listings matching zip/city
- [ ] Comps respects price range filters
- [ ] Price/sqft calculation matches manually computed expected value on seeded data
- [ ] Price/sqft handles zero `sqft` rows without crashing
- [ ] Days-on-market computed correctly from status history timestamps
- [ ] Agent summary counts match seeded fixture data exactly
- [ ] Listing report combines all three pieces (price, comps, DOM) without error
- [ ] Endpoints return 404/empty-safe responses when no matching data exists

### Phase 5 Completion Criteria

- [ ] Comps query returns listings within zip-based MVP radius
- [ ] Price/sqft calculation correct across filtered set, including edge cases
- [ ] Agent summary aggregates correctly against seeded data
- [ ] `pytest tests/test_analytics.py -v` — all green

---

## Phase 6 — Notifications

**Goal:** Trigger email (and optionally SMS) on key events: status changes, document sent, pipeline stage updates.

### 6.1 Infrastructure

- [ ] `app/tasks/celery_app.py` — Celery app configured with `REDIS_URL` as broker + backend
- [ ] `app/core/notifications.py`
  - [ ] `send_email(to, subject, body)` — SMTP client wrapper (Mailtrap creds from `.env`)
  - [ ] Template rendering for email bodies (can reuse Jinja2 env)
- [ ] `app/tasks/email_tasks.py`
  - [ ] `@celery_app.task` `send_status_change_email(listing_id, new_status)`
  - [ ] `@celery_app.task` `send_offer_submitted_email(pipeline_id)`
  - [ ] `@celery_app.task` `send_document_sent_email(document_id)`
  - [ ] `@celery_app.task` `send_pipeline_closed_email(pipeline_id)`
  - [ ] `@celery_app.task` `send_new_contact_assigned_email(contact_id)`
- [ ] `app/tasks/sms_tasks.py` (optional/stub) — same task shapes, no-op or Twilio stub

### 6.2 Wiring Triggers Into Existing Services

- [ ] `listing_service.change_status` enqueues `send_status_change_email`
- [ ] `pipeline_service.update_pipeline_entry` enqueues `send_offer_submitted_email` on transition into `offer_submitted`
- [ ] `pipeline_service.update_pipeline_entry` enqueues `send_pipeline_closed_email` on transition into `closed`
- [ ] `document_service.update_status` enqueues `send_document_sent_email` on transition into `sent`
- [ ] `contact_service.create_contact` enqueues `send_new_contact_assigned_email`

### 6.3 Idempotency & Reliability

- [ ] Each task checks/records a dedup key (e.g. `event_type + entity_id + target_status`) before sending, to survive retries
- [ ] Celery task `retry` configured with backoff + max retries
- [ ] Failures logged, not silently swallowed

### 6.4 Tests (`tests/test_notifications.py`)

- [ ] Celery worker (eager mode in tests) picks up and runs each task type
- [ ] Status change triggers email to agent + seller (mock SMTP, assert call args)
- [ ] Offer submitted triggers email to agent only
- [ ] Document sent triggers email to correct contact
- [ ] Pipeline closed triggers email to agent + both contacts
- [ ] New contact assigned triggers email to agent
- [ ] Re-running the same task twice does not send a duplicate email (idempotency check)
- [ ] Task retries on simulated SMTP failure, then succeeds

### Phase 6 Completion Criteria

- [ ] Celery worker starts and processes tasks from the queue
- [ ] Email sends correctly on every trigger event listed above (verified via mock SMTP in tests)
- [ ] Tasks are idempotent and safe to retry
- [ ] `pytest tests/test_notifications.py -v` — all green

---

## Cross-Cutting Concerns (apply throughout every phase)

- [ ] All IDs are UUID, generated server-side
- [ ] `created_at` / `updated_at` present on every model via shared `TimestampMixin`
- [ ] Role enforcement via FastAPI dependency (`require_role`), never inline in route handler bodies
- [ ] Services own all business logic — routers stay thin (parse input → call service → return schema)
- [ ] Every route has at least one happy-path test and one auth/permission-denied test
- [ ] Alembic migration generated and committed for every model change
- [ ] No bare `except:` blocks; errors surfaced as proper HTTP status codes
- [ ] Consistent error response shape across all routers
- [ ] `README.md` phase status table updated whenever a phase status marker changes