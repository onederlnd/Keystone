#
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.state_machine import LISTING_MACHINE
from backend.app.models.listing_status_history import ListingStatusHistory
from backend.app.models.listing import Listings
from backend.app.models.approval_queue import ApprovalQueue
from backend.app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingFilterParams,
)
from backend.app.models.audit_log import AuditLog
from backend.app.automation.hooks import fire_hook


async def create_listing(db: AsyncSession, data: ListingCreate):
    listing = Listings(**data.model_dump())

    db.add(listing)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Address already exists")

    await db.refresh(listing)

    log = AuditLog(
        entity_type="listing",
        entity_id=str(listing.id),
        action="created",
        triggered_by="manual",
        actor_id=None,
    )

    db.add(log)
    await db.commit()

    return listing


async def get_listing(db: AsyncSession, listing_id: uuid.UUID):
    result = await db.execute(select(Listings).where(Listings.id == listing_id))
    return result.scalar_one_or_none()


async def update_listing(db: AsyncSession, listing_id: uuid.UUID, data: ListingUpdate):
    result = await db.execute(select(Listings).where(Listings.id == listing_id))
    listing = result.scalar_one_or_none()

    if listing is None:
        return

    model = data.model_dump(exclude_unset=True)
    for k, v in model.items():
        setattr(listing, k, v)

    await db.commit()
    await db.refresh(listing)

    return listing


async def archive_listing(db: AsyncSession, listing_id: uuid.UUID):
    result = await db.execute(select(Listings).where(Listings.id == listing_id))
    listing = result.scalar_one_or_none()

    if listing is None:
        return

    listing.status = "archived"

    log = AuditLog(
        entity_type="listing",
        entity_id=str(listing.id),
        action="archive",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)

    await db.commit()

    return listing


async def list_listings(db: AsyncSession, data: ListingFilterParams):
    query = select(Listings)

    model = data.model_dump(exclude_unset=True)

    for k, v in model.items():
        if k == "max_price" and v is not None:
            query = query.where(Listings.price <= v)
        elif k == "min_price" and v is not None:
            query = query.where(Listings.price >= v)
        else:
            if v is not None:
                query = query.where(getattr(Listings, k) == v)

    result = await db.execute(query)

    listings = result.scalars().all()

    return listings


async def change_status(
    db: AsyncSession,
    listing_id: uuid.UUID,
    new_status: str,
    note: str,
    changed_by_id: uuid.UUID,
    triggered_by="manual",
):
    result = await db.execute(select(Listings).where(Listings.id == listing_id))

    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(404, "Listing not found")

    transition = LISTING_MACHINE.get_transition(listing.status, new_status)
    if transition is None:
        raise HTTPException(
            400, f"Cannot transition from {listing.status} to {new_status}"
        )

    if transition.requires_approval:
        approval = ApprovalQueue(
            entity_type="listing",
            entity_id=str(listing_id),
            proposed_action="change_status",
            proposed_state=new_status,
            context={
                "listing.id": str(listing.id),
                "previous_status": listing.status,
                "new_status": new_status,
                "changed_by_id": str(changed_by_id),
            },
            created_by=str(changed_by_id),
        )
        db.add(approval)
    else:
        status_history = ListingStatusHistory(
            listing_id=listing_id,
            previous_status=listing.status,
            new_status=new_status,
            changed_by_id=changed_by_id,
            notes=note,
            triggered_by=triggered_by,
        )

        listing.status = new_status

        db.add(status_history)

        log = AuditLog(
            entity_type="listing",
            entity_id=str(listing.id),
            action="update",
            triggered_by="automatic",
            actor_id=None,
        )
        db.add(log)

        context = {
            "listing.id": str(listing.id),
            "new_status": new_status,
            "changed_by_id": str(changed_by_id),
        }

        await fire_hook(f"listing.{new_status}", context)

    await db.commit()

    return listing


async def get_status_history(db: AsyncSession, listing_id: uuid.UUID):
    result = await db.execute(
        select(ListingStatusHistory).where(
            ListingStatusHistory.listing_id == listing_id
        )
    )
    return result.scalars().all()
