# backend/scripts/seed.py
"""
Populates the dev database with realistic demo data: users across all
roles, listings in every status, contacts, and pipeline entries spread
across every stage — enough to make the frontend look alive.

Run from the project root (same place you run ./run.sh):
    python -m backend.scripts.seed

Assumes migrations have already been run (alembic upgrade head) —
this script only inserts rows, it doesn't create tables.
"""

import asyncio
import uuid
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from backend.app.core.database import AsyncSessionLocal
from backend.app.core.security import hash_password
from backend.app.models.user import Users, UserRole
from backend.app.models.listing import Listings
from backend.app.models.contact import Contacts
from backend.app.models.pipeline import Pipelines


DEMO_PASSWORD = "password123"


async def seed():
    async with AsyncSessionLocal() as db:
        print("Seeding demo data...")

        existing = await db.execute(
            select(Users).where(Users.email == "admin@keystone.demo")
        )
        if existing.scalar_one_or_none():
            print(
                "Demo data already seeded - skipping. Delete realestate.db to reseed from scratch."
            )
            return

        # ---- Users ----
        admin = Users(
            email="admin@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Dana Ortiz",
            role=UserRole.admin,
            is_active=True,
        )
        agent_1 = Users(
            email="agent1@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Marcus Reid",
            role=UserRole.agent,
            is_active=True,
        )
        agent_2 = Users(
            email="agent2@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Priya Nandan",
            role=UserRole.agent,
            is_active=True,
        )
        seller_1 = Users(
            email="seller1@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Tom Whitfield",
            role=UserRole.seller,
            is_active=True,
        )
        seller_2 = Users(
            email="seller2@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Grace Lam",
            role=UserRole.seller,
            is_active=True,
        )
        buyer_1 = Users(
            email="buyer1@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Alex Chen",
            role=UserRole.buyer,
            is_active=True,
        )
        buyer_2 = Users(
            email="buyer2@keystone.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            full_name="Jordan Blake",
            role=UserRole.buyer,
            is_active=True,
        )

        users = [admin, agent_1, agent_2, seller_1, seller_2, buyer_1, buyer_2]
        db.add_all(users)
        await db.commit()
        for u in users:
            await db.refresh(u)

        # ---- Listings — one per status, split across both agents ----
        listings_data = [
            dict(
                agent=agent_1,
                seller=seller_1,
                address="118 Birchwood Ln",
                city="Royal Oak",
                state="MI",
                zip="48067",
                price=289000,
                bedrooms=3,
                bathrooms=2,
                sqft=1650,
                mls_id="MLS-1001",
                status="draft",
            ),
            dict(
                agent=agent_1,
                seller=seller_1,
                address="42 Maple Ct",
                city="Royal Oak",
                state="MI",
                zip="48067",
                price=315000,
                bedrooms=4,
                bathrooms=2,
                sqft=1900,
                mls_id="MLS-1002",
                status="active",
            ),
            dict(
                agent=agent_1,
                seller=seller_2,
                address="7 Harbor View Dr",
                city="Ferndale",
                state="MI",
                zip="48220",
                price=402000,
                bedrooms=3,
                bathrooms=3,
                sqft=2100,
                mls_id="MLS-1003",
                status="pending",
            ),
            dict(
                agent=agent_2,
                seller=seller_2,
                address="900 Woodward Ave #12",
                city="Detroit",
                state="MI",
                zip="48201",
                price=225000,
                bedrooms=2,
                bathrooms=1,
                sqft=1050,
                mls_id="MLS-1004",
                status="under_contract",
            ),
            dict(
                agent=agent_2,
                seller=seller_1,
                address="55 Lakeshore Blvd",
                city="Ferndale",
                state="MI",
                zip="48220",
                price=560000,
                bedrooms=5,
                bathrooms=4,
                sqft=3200,
                mls_id="MLS-1005",
                status="sold",
            ),
            dict(
                agent=agent_2,
                seller=seller_2,
                address="18 Birchwood Ln",
                city="Royal Oak",
                state="MI",
                zip="48067",
                price=270000,
                bedrooms=3,
                bathrooms=2,
                sqft=1500,
                mls_id="MLS-1006",
                status="off_market",
            ),
        ]

        listings = []
        for data in listings_data:
            listing = Listings(
                id=uuid.uuid4(),
                agent_id=data["agent"].id,
                seller_id=data["seller"].id,
                address=data["address"],
                city=data["city"],
                state=data["state"],
                zip=data["zip"],
                price=data["price"],
                bedrooms=data["bedrooms"],
                bathrooms=data["bathrooms"],
                sqft=data["sqft"],
                mls_id=data["mls_id"],
                status=data["status"],
                description=f"A well-kept {data['bedrooms']}-bed home in {data['city']}.",
            )
            db.add(listing)
            listings.append(listing)

        await db.commit()
        for l in listings:
            await db.refresh(l)

        # ---- Contacts — a couple of buyer leads per agent ----
        contacts_data = [
            dict(
                agent=agent_1,
                user=buyer_1,
                full_name="Alex Chen",
                email="buyer1@keystone.demo",
                phone="248-555-0101",
                type="buyer",
                source="referral",
            ),
            dict(
                agent=agent_1,
                user=None,
                full_name="Sam Ortega",
                email="sam.ortega@example.com",
                phone="248-555-0102",
                type="lead",
                source="website",
            ),
            dict(
                agent=agent_2,
                user=buyer_2,
                full_name="Jordan Blake",
                email="buyer2@keystone.demo",
                phone="313-555-0103",
                type="buyer",
                source="open house",
            ),
            dict(
                agent=agent_2,
                user=None,
                full_name="Nina Patel",
                email="nina.patel@example.com",
                phone="313-555-0104",
                type="lead",
                source="referral",
            ),
        ]

        contacts = []
        for data in contacts_data:
            contact = Contacts(
                id=uuid.uuid4(),
                agent_id=data["agent"].id,
                user_id=data["user"].id if data["user"] else data["agent"].id,
                full_name=data["full_name"],
                email=data["email"],
                phone=data["phone"],
                type=data["type"],
                source=data["source"],
            )
            db.add(contact)
            contacts.append(contact)

        await db.commit()
        for c in contacts:
            await db.refresh(c)

        # ---- Pipeline entries — spread across every stage ----
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        pipeline_data = [
            dict(
                listing=listings[1],
                contact=contacts[0],
                agent=agent_1,
                stage="new",
                offer_price=None,
                days_ago=1,
            ),
            dict(
                listing=listings[2],
                contact=contacts[1],
                agent=agent_1,
                stage="contacted",
                offer_price=None,
                days_ago=3,
            ),
            dict(
                listing=listings[1],
                contact=contacts[1],
                agent=agent_1,
                stage="showing_scheduled",
                offer_price=None,
                days_ago=5,
            ),
            dict(
                listing=listings[3],
                contact=contacts[2],
                agent=agent_2,
                stage="offer_submitted",
                offer_price=218000,
                days_ago=2,
            ),
            dict(
                listing=listings[2],
                contact=contacts[3],
                agent=agent_2,
                stage="negotiating",
                offer_price=395000,
                days_ago=6,
            ),
            dict(
                listing=listings[3],
                contact=contacts[3],
                agent=agent_2,
                stage="under_contract",
                offer_price=222000,
                days_ago=10,
            ),
            dict(
                listing=listings[4],
                contact=contacts[0],
                agent=agent_1,
                stage="closed",
                offer_price=555000,
                days_ago=30,
            ),
            dict(
                listing=listings[5],
                contact=contacts[2],
                agent=agent_2,
                stage="lost",
                offer_price=None,
                days_ago=15,
            ),
        ]

        for data in pipeline_data:
            entry = Pipelines(
                id=uuid.uuid4(),
                listing_id=data["listing"].id,
                contact_id=data["contact"].id,
                agent_id=data["agent"].id,
                stage=data["stage"],
                offer_price=data["offer_price"],
                last_stage_change_at=now - timedelta(days=data["days_ago"]),
            )
            db.add(entry)

        await db.commit()

        print("\nDone. Demo accounts (all use password: {}):".format(DEMO_PASSWORD))
        for u in users:
            print(f"  {u.role.value:8s} {u.email}")


if __name__ == "__main__":
    asyncio.run(seed())
