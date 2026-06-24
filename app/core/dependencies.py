from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    # TODO: Resolve the JWT token to a User model instance

    # Step 1: Call decode_access_token(token) — if it returns None, raise 401
    # Step 2: Extract the "sub" claim from the payload (this will be the user's id or email)
    # Step 3: Query the DB for the user — if not found, raise 401
    # Step 4: Return the user object
    # Tip: Use HTTPException(status_code=401, detail="...", headers={"WWW-Authenticate": "Bearer"})
    raise NotImplementedError


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(403, "Inactive user")

    return current_user


def require_role(*roles: str):
    # TODO: This is a dependency *factory* — it returns a dependency function, not a value
    # Step 1: Define an inner async function that depends on get_current_active_user

    # Step 2: Inside it, check if current_user.role is in the `roles` tuple
    # Step 3: If not, raise HTTPException 403 with detail "Insufficient permissions"
    # Step 4: If yes, return current_user
    # Step 5: Return the inner function (not the result of calling it)
    # Usage in a route: current_user = Depends(require_role("admin", "agent"))
    raise NotImplementedError
