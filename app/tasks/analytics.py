# app/tasks/analytics_tasks.py

import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.analytics import flag_stale_listings


async def _check_stale_listing():
    async with AsyncSessionLocal() as db:
        await flag_stale_listings(db, days_threshold=30)


@celery_app.task(name="tasks.run_stale_listing_check")
def check_stale_listing():
    asyncio.run(_check_stale_listing())
