# Contributing to Keystone

This document captures the conventions the codebase already follows. If you're adding a new phase, model, service, or hook, match these patterns rather than inventing new ones — consistency here matters more than local cleverness.

---

## Project Layout

- `app/models/` — SQLAlchemy ORM models only. No business logic.
- `app/schemas/` — Pydantic v2 request/response shapes.
- `app/routers/` — Thin FastAPI route handlers: parse request, call a service function, return. No business logic, no direct DB queries.
- `app/services/` — All business logic lives here. Routers call services; services own transitions, validation, and DB writes.
- `app/automation/` — Hook registry (`registry.py`, `hooks.py`) and hook implementations (e.g. `document_hooks.py`, `pipeline_hooks.py`). Organize hook files by **what the hook does**, not by what event triggers it — e.g. a hook that generates a document belongs in a document-related hooks file even if a `listing.*` event triggers it.
- `app/tasks/` — Celery background tasks.
- `app/templates/` — Jinja2 templates for PDF generation.

---

## Models

- All IDs are UUID, generated server-side: `id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, nullable=False)`.
- Every model inherits `TimestampMixin` for `created_at`/`updated_at`.
- `status`/`stage` fields are plain `str` columns, **not** DB-level enums. Validity is enforced at the service layer via the relevant `StateMachine` (`app/core/state_machine.py`), not by the database. This is intentional — see `listing_status_history.py` for the original precedent.
- Foreign keys that may not exist yet at creation time must be `nullable=True`, and the type hint must match: `Mapped[uuid.UUID | None]`, not `Mapped[uuid.UUID]`. Example: `Document.contact_id` and `Document.pipeline_id` are nullable because a `listing.active` event can generate a document before any pipeline/contact exists.
- Give every column with an obvious default a real default (`status: Mapped[str] = mapped_column(default="draft", ...)`), so forgetting to pass it explicitly fails safe rather than silently misrepresenting state.

---

## State Machines & Transitions

- Any entity with a status goes through its `StateMachine` (`LISTING_MACHINE`, `PIPELINE_MACHINE`, `DOCUMENT_MACHINE`) — never a raw enum/string write.
- `transition = SOME_MACHINE.get_transition(from_status, to_status)`; if `None`, raise `HTTPException(400, ...)`.
- **A `requires_approval` transition always writes to `ApprovalQueue`, regardless of `triggered_by`.** A manual API call doesn't get to skip the same review an automated action would need. If a transition shouldn't need review when done manually, that's a state-machine design change (`requires_approval=False`), not a service-layer bypass.
- `ApprovalQueue.created_by` only accepts `"automation"` or `"system"` — **never** `"manual"`. When a manual (`triggered_by="manual"`) action produces an approval-required transition, map it: `"system" if triggered_by == "manual" else "automation"`.
- Every transition writes to `AuditLog`, using the model's actual column names — `from_state`/`to_state`, not `from_status`/`to_status`.
- `fire_hook(transition.automation_hook, context)` is called **after** a successful, non-approval-required transition — never before, and never for transitions still sitting in the approval queue.

---

## Hooks & Automation

- Hooks are registered via `register_hook(event: str, fn)` in `app/automation/hooks.py`, stored as `REGISTRY[event] = [fn1, fn2, ...]` — **multiple hooks per event are supported and expected.** Registering a second hook against an existing event string does not overwrite the first.
- `fire_hook` supports both sync and async hook functions — it checks `inspect.iscoroutinefunction(fn)` and `await`s accordingly. If you add a new hook function, it can be `async def` or plain `def`; both work.
- Hook functions do not receive a `db` session — they open their own via `async with AsyncSessionLocal() as db:`. Never try to reuse a request-scoped session inside a hook.
- `context` dicts passed to hooks are plain primitives (IDs as strings, not ORM objects) — a hook must re-fetch any full rows it needs from the DB.
- When `AUTOMATION_ENABLED=False`, `fire_hook` is a no-op (logs intent, does not execute registered functions). Never special-case this inside a hook function itself — the kill switch lives in `fire_hook`, not in each hook.

---

## Document Generation Pattern

All auto-generated documents (`listing.active`, `pipeline.offer_submitted`, `pipeline.closed`, and any future document-producing hook) go through the shared helper:

```
app/services/document.py :: _generate_and_queue_document(
    db, template_name, doc_type, listing, contact, pipeline, agent, created_by_id
)
```

- `contact` and `pipeline` are optional (`None` when not yet available — e.g. a listing going active has no pipeline/contact yet). The helper handles `None` safely throughout, including in `create_document_record(...)` and the `ApprovalQueue.context` blob.
- Individual hook functions are responsible only for fetching the entities they have IDs for from `context`, then delegating everything else — record creation, rendering, PDF generation, file save, and approval-queue write — to this helper. **Do not duplicate the generation/queueing steps inline in a new hook function** — extend or call the shared helper instead.
- Every generated document is queued via `ApprovalQueue` (`proposed_action="send_document"`, `proposed_state="sent"`) rather than left to be discovered by browsing `GET /documents`. A document sitting at `status="draft"` alone does not satisfy "queued for review."
- Template context dicts always include whatever entities are available (`listing`, `agent`, `contact`, `pipeline`, `document_id`, `generated_at`) — Jinja2 silently ignores unused keys, so it's simpler to always pass the full set than to conditionally build the dict per template.
- Template variable naming is `generated_at`, not `generated_date` — keep this consistent across all four templates.

---

## Services

- Services own all business logic. Routers stay thin (parse, call service, return).
- Every mutating service function should accept an actor/trigger context (`actor_id`, `triggered_by`) rather than assuming who initiated the action — needed for accurate audit logging.
- Lookup functions (`get_document`, etc.) return `None` on not-found rather than raising; the caller decides whether that's a 404.
- Update functions that mutate then persist follow this order: fetch → check for `None` → mutate attribute → `db.commit()` → `db.refresh()` → return. `refresh()` before `commit()` will discard your in-memory change.

---

## Common Mistakes Worth Double-Checking

These have each shown up at least once during development — check for them specifically in review:

- **Truthy-string bugs**: `if "manual":` is always `True` — it checks whether the literal string is truthy, not whether some variable equals `"manual"`. Always compare explicitly: `if triggered_by == "manual":`.
- **Missing `await`** on `db.execute(...)` or any async service/helper call — produces a coroutine object instead of a result, fails silently or crashes downstream.
- **Type hints not matching `nullable=True`** — if a column is nullable, its `Mapped[...]` hint must include `| None`.
- **Calling an async hook function without `await`** — silently creates a coroutine and does nothing. `fire_hook` handles this correctly now; don't reintroduce the bug in a one-off caller elsewhere.
- **Copy-pasted `type=`/`template_name=` literals** left over from copying another hook (e.g. a `pipeline.closed` hook accidentally generating a `listing_agreement`).

---

## Tests

- Run phase-scoped tests during development: `pytest tests/test_documents.py tests/test_document_hooks.py -v` (adjust per phase).
- Every hook that writes to `ApprovalQueue` should have a test asserting the entry exists with the correct `entity_type`, `proposed_action`, and `created_by` value (never `"manual"`).
- Every new async hook should have a test confirming it actually executes (not just gets skipped) — this is exactly the class of bug that motivated the `fire_hook` coroutine fix.

---

## Keeping Docs in Sync

- `WORK_OUTLINE.md` is the source of truth for build status — treat it as authoritative over `README.md` when they disagree, and update both when a phase marker changes.
- If you add a template, helper, or fix that isn't explicitly listed as a checklist item in `WORK_OUTLINE.md` (e.g. the `_generate_and_queue_document` refactor, or the `fire_hook` async fix), add a short note under the relevant phase section anyway. Checkboxes should reflect what's actually on disk, not just what was originally scoped.