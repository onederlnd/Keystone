# app/services/analytics.py
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.listing import Listings
from app.automation.hooks import fire_hook
from app.models.listing_status_history import ListingStatusHistory


async def get_comps(db, zip, city, min_price, max_price):
    query = select(Listings)
    if zip:
        query = query.where(Listings.zip == zip)

    if city:
        query = query.where(Listings.city == city)

    if min_price:
        query = query.where(Listings.price >= min_price)

    if max_price:
        query = query.where(Listings.price <= max_price)

    result = await db.execute(query)
    listings = result.scalars().all()

    return listings


async def get_price_per_sqft(db, zip=None, city=None):
    query = select(Listings)
    if zip:
        query = query.where(Listings.zip == zip)

    if city:
        query = query.where(Listings.city == city)

    result = await db.execute(query)
    listings = result.scalars().all()

    values = [l.price / l.sqft for l in listings if l.sqft != 0]
    if not values:
        return

    return sum(values) / len(values)


async def get_days_on_market(db, zip=None, city=None):
    query = select(Listings).where(Listings.status == "sold")

    if zip:
        query = query.where(Listings.zip == zip)

    if city:
        query = query.where(Listings.city == city)

    result = await db.execute(query)
    listings = result.scalars().all()

    results = []

    for listing in listings:
        active_query = (
            select(ListingStatusHistory)
            .where(
                ListingStatusHistory.listing_id == listing.id,
                ListingStatusHistory.new_status == "active",
            )
            .order_by(ListingStatusHistory.created_at)
            .limit(1)
        )
        active_result = await db.execute(active_query)
        active_listing = active_result.scalar_one_or_none()

        sold_query = (
            select(ListingStatusHistory)
            .where(
                ListingStatusHistory.listing_id == listing.id,
                ListingStatusHistory.new_status == "sold",
            )
            .order_by(ListingStatusHistory.created_at)
            .limit(1)
        )
        sold_result = await db.execute(sold_query)
        sold_listing = sold_result.scalar_one_or_none()

        if active_listing and sold_listing:
            days_on_market = (sold_listing.created_at - active_listing.created_at).days
        else:
            days_on_market = None

        results.append({"listing": listing, "days_on_market": days_on_market})

    return results


async def get_agent_summary(db, agent_id):
    query = select(Listings)
    if agent_id:
        query = query.where(Listings.agent_id == agent_id)

    result = await db.execute(query)
    listings = result.scalars().all()

    values = [listing.price for listing in listings]
    if not values:
        return {"count": 0, "average_price": None}

    average_price = sum(values) / len(values)

    return {"count": len(values), "average_price": average_price}


async def get_listing_report(db, listing_id):
    result = await db.execute(select(Listings).where(Listings.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing is None:
        return

    comps = await get_comps(
        db, zip=listing.zip, city=listing.city, min_price=None, max_price=None
    )

    dom_results = await get_days_on_market(db, zip=listing.zip, city=listing.city)
    dom_entry = next((r for r in dom_results if r["listing"].id == listing_id), None)

    return {
        "listing": listing,
        "price": listing.price,
        "comps": comps,
        "days_on_market": dom_entry["days_on_market"] if dom_entry else None,
    }


async def flag_stale_listings(db, days_threshold):
    query = select(Listings).where(Listings.status == "active")
    result = await db.execute(query)

    listings = result.scalars().all()

    stale_listings = []

    for listing in listings:
        query = (
            select(ListingStatusHistory)
            .where(ListingStatusHistory.listing_id == listing.id)
            .order_by(ListingStatusHistory.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        listing_history = result.scalar_one_or_none()

        if listing_history is None:
            continue

        listing_age = (
            datetime.now(timezone.utc).replace(tzinfo=None) - listing_history.created_at
        )

        if listing_age.days > days_threshold:
            context = {"listing_id": str(listing.id)}

            await fire_hook("listing.stale", context)

            stale_listings.append(listing)

    return stale_listings


async def flag_price_outliers(db, zip, threshold_pct):
    query = select(Listings).where(Listings.zip == zip)
    result = await db.execute(query)
    listings = result.scalars().all()

    if not listings:
        return []

    price_outliers = []
    listings_avg_price = sum(l.price for l in listings) / len(listings)

    for listing in listings:
        percent_difference = (
            (listing.price - listings_avg_price) / listings_avg_price * 100
        )
        if abs(percent_difference) > threshold_pct:
            context = {"listing_id": str(listing.id)}
            await fire_hook("listing.price_alert", context)

            price_outliers.append(listing)

    return price_outliers
