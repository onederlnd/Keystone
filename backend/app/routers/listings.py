# app/routers/listings.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.listing import (
    create_listing,
    get_listing,
    update_listing,
    archive_listing,
    list_listings,
    change_status,
    get_status_history,
)
from backend.app.schemas.listing import (
    ListingRead,
    ListingUpdate,
    ListingCreate,
    ListingFilterParams,
    ListingStatusUpdate,
    ListingStatusHistoryRead,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingRead)
async def create_listing_route(
    data: ListingCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_listing(db, data)


@router.get("/", response_model=list[ListingRead])
async def list_listings_route(
    filters: ListingFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    listings = await list_listings(db, filters)
    if not listings:
        raise HTTPException(404, "Listing not found")
    return listings


@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing_route(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    listing = await get_listing(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@router.patch("/{listing_id}", response_model=ListingRead)
async def update_listing_route(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    db: AsyncSession = Depends(get_db),
):
    listing = await update_listing(db, listing_id, data)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@router.patch("/{listing_id}/status", response_model=ListingRead)
async def change_status_route(
    listing_id: uuid.UUID, data: ListingStatusUpdate, db: AsyncSession = Depends(get_db)
):
    listing = await change_status(
        db,
        listing_id,
        data.new_status,
        data.notes,
        data.changed_by_id,
        data.triggered_by,
    )
    if not listing:
        raise HTTPException(404, "Listing not found")

    return listing


@router.patch("/{listing_id}/archive")
async def archive_listing_route(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    listing = await archive_listing(db, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@router.get(
    "/{listing_id}/status-history", response_model=list[ListingStatusHistoryRead]
)
async def get_status_history_route(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    status_history = await get_status_history(db, listing_id)
    if not status_history:
        raise HTTPException(404, "Status history not found.")
    return status_history
