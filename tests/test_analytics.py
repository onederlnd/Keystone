# tests/test_analytics.py

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.user import UserRole
from app.models.listing_status_history import ListingStatusHistory
from app.services.analytics import (
    get_comps,
    get_price_per_sqft,
    get_days_on_market,
    get_agent_summary,
    get_listing_report,
    flag_stale_listings,
    flag_price_outliers,
)


def _headers_for(user):
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


async def _add_history(db_session, listing_id, new_status, created_at, changed_by_id):
    status_history = ListingStatusHistory(
        listing_id=listing_id,
        previous_status="draft",
        new_status=new_status,
        changed_by_id=changed_by_id,
        notes=None,
        triggered_by="manual",
        created_at=created_at,
    )
    db_session.add(status_history)

    await db_session.commit()
    await db_session.refresh(status_history)

    return status_history


@pytest.mark.asyncio
async def test_get_comps_filters_by_zip(db_session, create_listing_in_db):
    match = await create_listing_in_db(zip="48201", price=250000)
    await create_listing_in_db(zip="90210", price=250000)

    results = await get_comps(
        db_session, zip="48201", city=None, min_price=None, max_price=None
    )

    ids = [l.id for l in results]
    assert match.id in ids
    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_comps_filters_by_price_range(db_session, create_listing_in_db):
    low = await create_listing_in_db(price=100000)
    mid = await create_listing_in_db(price=250000)
    high = await create_listing_in_db(price=500000)

    results = await get_comps(
        db_session, zip=None, city=None, min_price=150000, max_price=300000
    )

    ids = [l.id for l in results]
    assert mid.id in ids
    assert low.id not in ids
    assert high.id not in ids


@pytest.mark.asyncio
async def test_get_price_per_sqft_computes_average(db_session, create_listing_in_db):
    await create_listing_in_db(zip="48899", price=200000, sqft=1000)  # 200/sqft
    await create_listing_in_db(zip="48899", price=400000, sqft=1000)  # 400/sqft

    result = await get_price_per_sqft(db_session, zip="48899")
    assert result == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_get_price_per_sqft_no_matches_returns_none(db_session):
    result = await get_price_per_sqft(db_session, zip="00000")
    assert result is None


@pytest.mark.asyncio
async def test_get_days_on_market_computes_days(
    db_session, create_listing_in_db, create_user_in_db
):
    agent = await create_user_in_db(
        email=f"dom-{uuid.uuid4()}@test.com", role=UserRole.agent
    )
    listing = await create_listing_in_db(status="sold")

    active_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=20)
    sold_time = datetime.now(timezone.utc).replace(tzinfo=None)

    await _add_history(db_session, listing.id, "active", active_time, agent.id)
    await _add_history(db_session, listing.id, "sold", sold_time, agent.id)

    results = await get_days_on_market(db_session)
    entry = next((r for r in results if r["listing"].id == listing.id), None)

    assert entry is not None
    assert entry["days_on_market"] == 20


@pytest.mark.asyncio
async def test_get_days_on_market_missing_history_returns_none(
    db_session, create_listing_in_db
):
    listing = await create_listing_in_db(status="sold")

    results = await get_days_on_market(db_session)
    entry = next((r for r in results if r["listing"].id == listing.id), None)

    assert entry is not None
    assert entry["days_on_market"] is None


@pytest.mark.asyncio
async def test_get_agent_summary_counts_and_averages(
    db_session, create_user_in_db, create_listing_in_db
):
    agent = await create_user_in_db(
        email=f"summary-{uuid.uuid4()}@test.com", role=UserRole.agent
    )
    await create_listing_in_db(agent=agent, price=100000)
    await create_listing_in_db(agent=agent, price=300000)

    summary = await get_agent_summary(db_session, agent.id)

    assert summary["count"] == 2
    assert summary["average_price"] == pytest.approx(200000.0)


@pytest.mark.asyncio
async def test_get_agent_summary_no_listings_returns_zero(
    db_session, create_user_in_db
):
    agent = await create_user_in_db(
        email=f"noagent-{uuid.uuid4()}@test.com", role=UserRole.agent
    )

    summary = await get_agent_summary(db_session, agent.id)

    assert summary == {"count": 0, "average_price": None}


@pytest.mark.asyncio
async def test_get_listing_report_combines_data(db_session, create_listing_in_db):
    listing = await create_listing_in_db()

    report = await get_listing_report(db_session, listing.id)

    assert report["listing"].id == listing.id
    assert report["price"] == listing.price
    assert "comps" in report
    assert "days_on_market" in report


@pytest.mark.asyncio
async def test_get_listing_report_not_found_returns_none(db_session):
    report = await get_listing_report(db_session, uuid.uuid4())
    assert report is None


@pytest.mark.asyncio
async def test_flag_stale_listings_flags_only_qualifying(
    db_session, create_listing_in_db, create_user_in_db, monkeypatch
):
    from unittest.mock import AsyncMock

    mock_fire_hook = AsyncMock()
    monkeypatch.setattr("app.services.analytics.fire_hook", mock_fire_hook)

    agent = await create_user_in_db(
        email=f"stale-{uuid.uuid4()}@test.com", role=UserRole.agent
    )

    stale_listing = await create_listing_in_db(status="active")
    fresh_listing = await create_listing_in_db(status="active")

    old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60)
    recent_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

    await _add_history(db_session, stale_listing.id, "active", old_time, agent.id)
    await _add_history(db_session, fresh_listing.id, "active", recent_time, agent.id)

    result = await flag_stale_listings(db_session, days_threshold=30)

    result_ids = [l.id for l in result]
    assert stale_listing.id in result_ids
    assert fresh_listing.id not in result_ids
    mock_fire_hook.assert_called_once()
    assert mock_fire_hook.call_args[0][0] == "listing.stale"


@pytest.mark.asyncio
async def test_flag_price_outliers_flags_only_outliers(
    db_session, create_listing_in_db, monkeypatch
):
    from unittest.mock import AsyncMock

    mock_fire_hook = AsyncMock()
    monkeypatch.setattr("app.services.analytics.fire_hook", mock_fire_hook)

    zip_code = f"{uuid.uuid4().int % 100000:05d}"
    normal_a = await create_listing_in_db(zip=zip_code, price=200000)
    normal_b = await create_listing_in_db(zip=zip_code, price=210000)
    outlier = await create_listing_in_db(zip=zip_code, price=300000)

    result = await flag_price_outliers(db_session, zip=zip_code, threshold_pct=20)

    result_ids = [l.id for l in result]
    assert outlier.id in result_ids
    assert normal_a.id not in result_ids
    assert normal_b.id not in result_ids
    mock_fire_hook.assert_called_once()
    assert mock_fire_hook.call_args[0][0] == "listing.price_alert"


@pytest.mark.asyncio
async def test_comps_route(client, create_listing_in_db, create_user_in_db):
    user = await create_user_in_db(
        email=f"comproute-{uuid.uuid4()}@test.com", role=UserRole.agent
    )
    listing = await create_listing_in_db(zip="55555")

    response = await client.get(
        "/analytics/comps?zip=55555", headers=_headers_for(user)
    )
    assert response.status_code == 200
    ids = [l["id"] for l in response.json()]
    assert str(listing.id) in ids


@pytest.mark.asyncio
async def test_agent_summary_route(client, create_user_in_db, create_listing_in_db):
    agent = await create_user_in_db(
        email=f"sumroute-{uuid.uuid4()}@test.com", role=UserRole.agent
    )
    await create_listing_in_db(agent=agent, price=150000)

    response = await client.get(
        f"/analytics/agent/{agent.id}/summary", headers=_headers_for(agent)
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.asyncio
async def test_listing_report_route_not_found(client, create_user_in_db):
    user = await create_user_in_db(
        email=f"reportroute-{uuid.uuid4()}@test.com", role=UserRole.agent
    )

    response = await client.get(
        f"/analytics/listings/{uuid.uuid4()}/report", headers=_headers_for(user)
    )
    assert response.status_code == 404
