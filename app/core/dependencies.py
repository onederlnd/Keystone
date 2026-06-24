from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(401, "WWW-Authentication: Bearer header")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(401, "Email or ID missing")

    user = 0  # TODO
    if not user:
        raise HTTPException(401, "User not found")

    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(403, "Inactive account")

    return current_user


def require_role(*roles):
    def _is_role(current_user=Depends(get_current_active_user)):
        if current_user.role in roles:
            return current_user
        else:
            raise HTTPException(403, "User not correct role")

    return _is_role()


async def get_approval_queue_entry(id, db: AsyncSession = Depends(get_db)):
    # STUB: Phase 7 — not implemented yet
    raise HTTPException(404, "Current endpoint is not yet available")
