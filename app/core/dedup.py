# app/core/dedup.py

import redis.asyncio as redis
from app.core.config import settings
from app.tasks.email_tasks import send_listing_status_email

redis_client = redis.from_url(settings.redis_url)

DEDUP_TTL_SECONDS = 60


def build_dedup_key(event_type, entity_id, target_state):
    return f"dedup: {event_type}:{entity_id}:{target_state}"


async def is_duplicate(event_type, entity_id, target_state):
    key = build_dedup_key(event_type, entity_id, target_state)
    was_set = await redis_client.set(key, "1", nx=True, ex=DEDUP_TTL_SECONDS)
    return was_set
