# app/routers/analytics.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db

from backend.app.services.analytics import (
    get_comps,
    get_agent_summary,
    get_days_on_market,
    get_listing_report,
    get_price_per_sqft,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/comps")
async def get_comps_route(
    zip: str | None = None,
    city: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await get_comps(db, zip, city, min_price, max_price)


@router.get("/price-per-sqft")
async def get_price_per_sqft_route(
    zip: str | None = None, city: str | None = None, db: AsyncSession = Depends(get_db)
):
    return await get_price_per_sqft(db, zip, city)


@router.get("/days-on-market")
async def get_days_on_market_route(
    zip: str | None = None, city: str | None = None, db: AsyncSession = Depends(get_db)
):
    return await get_days_on_market(db, zip, city)


@router.get("/agent/{id}/summary")
async def get_agent_summary_route(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_agent_summary(db, id)


@router.get("/listings/{id}/report")
async def get_listing_report_route(id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    listing = await get_listing_report(db, id)
    if listing is None:
        raise HTTPException(404, "Listing report not found")

    return listing
