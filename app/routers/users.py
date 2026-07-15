# app/routers/users.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.schemas.user import UserRead, UserUpdate
from app.services.user import get_user_by_id, update_user, deactivate_user
from app.models.user import Users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(current_user: Users = Depends(get_current_user)):
    return current_user


@router.get("/{id}", response_model=UserRead)
async def get_user(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    user = await get_user_by_id(db, id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.patch("/{id}", response_model=UserRead)
async def patch_user(
    id: uuid.UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    user = await update_user(db, id, user_data)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(require_role("admin")),
):
    user = await deactivate_user(db, id)
    if not user:
        raise HTTPException(404, "User not found")
