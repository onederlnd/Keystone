# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import (
    analytics,
    auth,
    contacts,
    documents,
    listings,
    approval_queue,
    users,
    pipeline,
)
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(title=settings.api_title)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(listings.router)
app.include_router(contacts.router)
app.include_router(pipeline.router)
app.include_router(documents.router)
app.include_router(analytics.router)
app.include_router(approval_queue.router)


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}
