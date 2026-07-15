# tests/conftest.py

import uuid
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import hash_password, create_access_token
from backend.app.models.user import Users, UserRole
from backend.app.models.pipeline import Pipelines
from backend.app.models.contact import Contacts
from backend.app.models.listing import Listings
from backend.app.tasks.celery_app import celery_app

from backend.app.models.document import Documents

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
        user = Users(
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
        listing = Listings(**defaults)

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

        contact = Contacts(
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
        entry = Pipelines(**defaults)
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
        contact = Contacts(**defaults)

        db_session.add(contact)

        await db_session.commit()
        await db_session.refresh(contact)

        return contact, agent

    return _create


@pytest_asyncio.fixture
async def create_document_in_db(
    db_session,
    create_listing_in_db,
    create_contact_in_db,
    create_pipeline_in_db,
    create_user_in_db,
):
    async def _create(
        created_by=None, listing=None, contact=None, pipeline=None, **overrides
    ):
        if created_by is None:
            created_by = await create_user_in_db(
                email=f"doc-owner-{uuid.uuid4()}@test.com", role=UserRole.agent
            )
        if listing is None:
            listing = await create_listing_in_db()
        if contact is None:
            contact, _ = await create_contact_in_db()
        if pipeline is None:
            pipeline = await create_pipeline_in_db()

        defaults = {
            "id": uuid.uuid4(),
            "listing_id": listing.id,
            "contact_id": contact.id,
            "pipeline_id": pipeline.id,
            "created_by_id": created_by.id,
            "type": "listing_agreement",
            "file_path": f"/tmp/{uuid.uuid4()}.pdf",
            "generated_by": "manual",
            "status": "draft",
        }
        defaults.update(overrides)
        document = Documents(**defaults)
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        return document, created_by

    return _create


@pytest_asyncio.fixture(autouse=True)
async def task_eager_mode():
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
    yield
    celery_app.conf.update(task_always_eager=False, task_eager_propagates=False)


@pytest_asyncio.fixture(autouse=True)
def reset_hook_registry():
    from backend.app.automation.registry import REGISTRY

    REGISTRY.clear()
    yield
    REGISTRY.clear()


@pytest_asyncio.fixture
async def patch_async_session_local(monkeypatch):
    """
    Hooks (document_hooks.py, pipeline_hooks.py) open their own session via
    app.core.database.AsyncSessionLocal instead of reusing a request-scoped
    session. Point that sessionmaker at the test engine, or hook writes land
    in an unrelated database.
    """
    monkeypatch.setattr("backend.app.core.database.AsyncSessionLocal", TestSessionLocal)
    yield
