# Keystone — Frontend

A React (Vite) frontend for the Keystone backend, covering everything built through Phase 5: auth, listings, contacts/CRM, the deal pipeline, documents, and analytics.

## Setup

```bash
npm install
cp .env.example .env    # point VITE_API_BASE_URL at your running backend
npm run dev
```

Make sure your FastAPI backend has CORS configured to allow `http://localhost:5173` (Vite's default dev port).

## What's here

| Screen | Route | Backend endpoints used |
| --- | --- | --- |
| Login | `/login` | `POST /auth/login`, `GET /users/me` |
| Dashboard | `/` | `GET /listings/`, `GET /analytics/agent/{id}/summary` |
| Listings | `/listings`, `/listings/:id` | `GET/PATCH /listings/*` |
| Contacts | `/contacts` | `GET/POST /contacts/` |
| Pipeline | `/pipeline` | `GET /pipeline/`, `PATCH /pipeline/{id}` |
| Documents | `/documents` | `GET /documents/`, `GET /documents/{id}/download`, `POST /documents/{id}/status` |
| Analytics | `/analytics` | `GET /analytics/*` |

## Assumptions worth checking against your real API

I don't have your actual Pydantic schemas in front of me, so a few things are best-guess and may need small tweaks once you run this against the real backend:

- **`POST /auth/login`** — assumed to accept JSON `{ email, password }` and return `{ access_token, token_type }`. If your login route expects OAuth2 form-encoded data instead (FastAPI's `OAuth2PasswordRequestForm` default), `api/client.js`'s `login()` function needs to send `FormData` instead of JSON.
- **Listing/pipeline/document field names** — the frontend expects fields like `address`, `city`, `price`, `bedrooms`, `bathrooms`, `sqft`, `mls_id` on listings; `contact_name`, `offer_price`, `stage` on pipeline entries; `type`, `status`, `generated_by` on documents. These match what was built during the backend conversation, but double-check against your actual `Read` schemas.
- **Status-change response shape** — when a transition requires approval, the code checks for `result.status === "pending"` to distinguish an `ApprovalQueue` entry from a normal updated object. Confirm this against your actual `ApprovalQueueRead` schema — the field might be named differently.
- **`ListingStatusHistory` timestamp field** — the history table renders `h.changed_at || h.created_at`, since earlier in the backend build this ended up being `created_at` rather than a dedicated `changed_at` column. Adjust if yours differs.

## What's intentionally not built yet

**The Approval Queue screen.** This is arguably the most important screen in the whole app — the place agents review and override everything automation proposes — but it depends on Phase 7 of the backend (`GET /approval-queue/`, `POST /approval-queue/{id}/approve|reject|modify`), which hasn't been built yet. Right now, approval-required actions surface as an inline message on the Listings/Pipeline/Documents pages ("this requires approval and has been queued for review") but there's nowhere to actually go review and act on that queue. Build this once Phase 7 lands — it's the natural next screen.

**Document generation UI.** There's no "generate a document manually" form yet (`POST /documents`) — documents currently only show up via the automation hooks. Worth adding if agents need to trigger one-off generation outside the automated flow.

**Admin rule management.** Phase 7's `automation_rules` CRUD has no corresponding UI, for the same reason — the backend isn't built yet.

## Design notes

The visual direction ("the closing table") uses a navy/brass/paper palette meant to evoke a working transaction ledger rather than a marketing site — Fraunces for headers, Inter for body text, IBM Plex Mono for anything numeric (prices, MLS IDs, dates) so data reads distinctly from prose. The pipeline board's numbered columns reflect the actual ordered transaction sequence, not decoration. All of this lives in `src/index.css` as CSS custom properties if you want to adjust it.
