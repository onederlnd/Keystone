# tests/conftest.py

import uuid
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.pipeline import Pipeline
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
async def auth_headers(create_user_in_db):
    async def _headers(role=UserRole.buyer):
        user = await create_user_in_db(email=f"{role.value}@test.com", role=role)
        token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    return _headers


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
async def create_listing_in_db(db_session, create_user_in_db):
    async def _create(agent=None, seller=None, **overrides):
        if not agent:
            agent = await create_user_in_db(
                email=f"agent-{uuid.uuid4()}@test.com", role=UserRole.agent
            )
        if not seller:
            seller = await create_user_in_db(
                email=f"seller-{uuid.uuid4()}@test.com", role=UserRole.seller
            )
        from app.models.listing import Listing

        defaults = {
            "agent_id": agent.id,
            "seller_id": seller.id,
            "address": f"{uuid.uuid4()} Main St",
            "city": "Detroit",
            "state": "MI",
            "zip": "48201",
            "price": 250000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1500,
            "mls_id": f"MLS-{uuid.uuid4()}",
        }
        defaults.update(overrides)
        listing = Listing(**defaults)

        db_session.add(listing)

        await db_session.commit()
        await db_session.refresh(listing)

        return listing

    return _create


@pytest_asyncio.fixture
async def create_pipeline_in_db(db_session, create_listing_in_db, create_user_in_db):
    async def _create(stage="new", **overrides):
        listing = await create_listing_in_db()
        agent = await create_user_in_db(email=f"pipe-agent-{uuid.uuid4()}@test.com")
        from app.models.contact import Contact

        contact = Contact(
            agent_id=agent.id,
            user_id=agent.id,
            full_name="Pipeline Lead",
            email=f"pipelead-{uuid.uuid4()}@test.com",
            phone="555-0199",
            type="buyer",
            source="referral",
        )
        db_session.add(contact)
        await db_session.commit()
        await db_session.refresh(contact)

        defaults = {
            "listing_id": listing.id,
            "contact_id": contact.id,
            "agent_id": agent.id,
            "stage": stage,
        }
        defaults.update(overrides)
        entry = Pipeline(**defaults)
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)
        return entry

    return _create


@pytest_asyncio.fixture
async def create_contact_in_db(db_session, create_user_in_db):
    async def _create(agent=None, **overrides):
        if not agent:
            agent = await create_user_in_db(
                email=f"agent-{uuid.uuid4()}@test.com", role=UserRole.agent
            )
        from app.models.contact import Contact

        defaults = {
            "agent_id": agent.id,
            "user_id": agent.id,
            "full_name": "Jane Prospect",
            "email": f"prospect-{uuid.uuid4()}@test.com",
            "phone": "555-0100",
            "type": "buyer",
            "source": "website",
        }
        defaults.update(overrides)
        contact = Contact(**defaults)
        db_session.add(contact)
        await db_session.commit()
        await db_session.refresh(contact)
        return contact, agent

    return _create


@pytest_asyncio.fixture(autouse=True)
def reset_hook_registry():
    from app.automation.registry import REGISTRY

    REGISTRY.clear()
    yield
    REGISTRY.clear()
