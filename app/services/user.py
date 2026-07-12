# app/services/user.py

import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Users
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from app.models.audit_log import AuditLog


async def create_user(db: AsyncSession, user_data: UserCreate):
    user = Users(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Email already registered")

    await db.refresh(user)

    log = AuditLog(
        entity_type="user",
        entity_id=str(user.id),
        action="created",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)
    await db.commit()

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
):
    result = await db.execute(select(Users).where(Users.email == email))

    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return

    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(Users).where(Users.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(Users).where(Users.email == email))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: uuid.UUID, user_data: UserUpdate):
    result = await db.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return

    if user_data.full_name:
        user.full_name = user_data.full_name

    if user_data.email:
        user.email = user_data.email

    if user_data.password:
        user.hashed_password = hash_password(user_data.password)

    await db.commit()
    await db.refresh(user)

    log = AuditLog(
        entity_type="user",
        entity_id=str(user.id),
        action="updated",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)
    await db.commit()

    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID):
    result = await db.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return

    user.is_active = False

    await db.commit()

    log = AuditLog(
        entity_type="user",
        entity_id=str(user.id),
        action="deactivated",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)
    await db.commit()

    return user
