from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users

# TODO: Instantiate the FastAPI app
#       - Set a title like "Keystone API"
app = FastAPI(title="Keystone API")

# TODO: Add CORSMiddleware
#       - allow_origins: read from settings or use ["*"] for dev
#       - allow_credentials=True
#       - allow_methods=["*"]
#       - allow_headers=["*"]


# TODO: Register routers
#       - app.include_router(auth.router)
#       - app.include_router(users.router)


@app.get("/health", status_code=200)
async def health_check():
    # TODO: Return a simple dict like {"status": "ok"}
    raise NotImplementedError
