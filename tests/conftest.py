# tests/conftest.py

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_user_in_db(db_session):
    async def _create(
        email="test@test.com", password="password123", role=UserRole.buyer
    ):
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="Test User",
            role=role,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def auth_headers(create_user_in_db):
    async def _headers(role=UserRole.buyer):
        user = await create_user_in_db(email=f"{role.value}@test.com", role=role)
        token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    return _headers
