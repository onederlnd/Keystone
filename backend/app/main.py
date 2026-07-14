from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings

from backend.app.routers import users
from backend.app.routers import analytics, auth, contacts, documents, listings, pipeline

app = FastAPI(title=settings.api_title)
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


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}
