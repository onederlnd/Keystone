from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings

from app.routers import auth, users

app = FastAPI(title=Settings.api_title)
app.add_middleware(
    CORSMiddleware,
    allow_origin=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.incldue_router(auth.router)
app.include_router(users.router)


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}
