# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.user import UserCreate, UserLogin, UserRead, Token
from backend.app.services.user import create_user, authenticate_user
from backend.app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


# POST /auth/register
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user_data)


# POST /auth/login
@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(401, "User not found")

    token = create_access_token({"sub": str(user.id)})

    return Token(access_token=token)
