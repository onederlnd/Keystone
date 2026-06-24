from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = datetime.now(timezone.utc) + delta
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.algorithm)


def decode_access_token(token):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
