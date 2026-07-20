# tests/test_notifications.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from celery.exceptions import Retry
from sqlalchemy import select
from app.models.audit_log import AuditLog
from app.tasks.email_tasks import (
    send_listing_status_email,
)
from app.automation.notification_hooks import (
    on_listing_active,
    on_pipeline_offer_submitted,
    on_document_sent,
    on_contact_created,
)


# ---------------------------------------------------------------------------
# 1. Each hook fires the correct Celery task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_listing_active_fires_send_listing_status_email(create_listing_in_db):
    listing = await create_listing_in_db()
    context = {"listing_id": listing.id}

    with (
        patch(
            "app.automation.notification_hooks.send_listing_status_email.delay"
        ) as mock_delay,
        patch(
            "app.automation.notification_hooks.is_duplicate",
            new=AsyncMock(return_value=False),
        ),
    ):
        await on_listing_active(context)

    assert mock_delay.call_count == 2
    mock_delay.assert_any_call(listing.id, "agent", entity_type="listing")
    mock_delay.assert_any_call(listing.id, "seller", entity_type="listing")


@pytest.mark.asyncio
async def test_on_document_sent_fires_send_document_ready_email(create_document_in_db):
    document, _ = await create_document_in_db()
    context = {"document_id": document.id}

    with (
        patch(
            "app.automation.notification_hooks.send_document_ready_email.delay"
        ) as mock_delay,
        patch(
            "app.automation.notification_hooks.is_duplicate",
            new=AsyncMock(return_value=False),
        ),
    ):
        await on_document_sent(context)

    mock_delay.assert_called_once_with(document.id, entity_type="document")


# ---------------------------------------------------------------------------
# 2. Correct recipients per event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_pipeline_offer_submitted_notifies_agent_and_contact(
    create_pipeline_in_db,
):
    pipeline = await create_pipeline_in_db()
    context = {"pipeline_id": pipeline.id}

    with (
        patch(
            "app.automation.notification_hooks.send_pipeline_stage_email.delay"
        ) as mock_delay,
        patch(
            "app.automation.notification_hooks.is_duplicate",
            new=AsyncMock(return_value=False),
        ),
    ):
        await on_pipeline_offer_submitted(context)

    roles_called = {call.args[1] for call in mock_delay.call_args_list}
    assert roles_called == {"agent", "contact"}


@pytest.mark.asyncio
async def test_on_contact_created_notifies_agent_only(create_contact_in_db):
    contact, _ = await create_contact_in_db()
    context = {"contact_id": contact.id}

    with (
        patch(
            "app.automation.notification_hooks.send_new_contact_email.delay"
        ) as mock_delay,
        patch(
            "app.automation.notification_hooks.is_duplicate",
            new=AsyncMock(return_value=False),
        ),
    ):
        await on_contact_created(context)

    mock_delay.assert_called_once_with(contact.id, entity_type="contact")


# ---------------------------------------------------------------------------
# 3. Idempotency — running the same event twice sends only once
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_event_does_not_fire_twice(create_listing_in_db):
    listing = await create_listing_in_db()
    context = {"listing_id": listing.id}

    with (
        patch(
            "app.automation.notification_hooks.send_listing_status_email.delay"
        ) as mock_delay,
        patch(
            "app.automation.notification_hooks.is_duplicate",
            new=AsyncMock(side_effect=[False, False, True, True]),
        ),
    ):
        await on_listing_active(context)  # fires twice (agent, seller)
        await on_listing_active(context)  # both skipped as duplicates

    assert mock_delay.call_count == 2


# ---------------------------------------------------------------------------
# 4. Retry on SMTP failure, succeeds on second attempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_listing_status_email_retries_on_smtp_failure(
    create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db()

    with patch(
        "app.tasks.email_tasks.send_email",
        new=AsyncMock(side_effect=[Exception("SMTP down"), None]),
    ) as mock_send:
        try:
            await asyncio.to_thread(
                send_listing_status_email.apply,
                args=[listing.id, "agent"],
                kwargs={"entity_type": "listing"},
            )
        except Retry:
            await asyncio.to_thread(
                send_listing_status_email.apply,
                args=[listing.id, "agent"],
                kwargs={"entity_type": "listing"},
            )
    assert mock_send.call_count == 2


# ---------------------------------------------------------------------------
# 5. Failure writes audit log entry
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notification_failure_writes_audit_log(
    create_listing_in_db, patch_async_session_local, db_session
):
    listing = await create_listing_in_db()
    exc = Exception("SMTP permanently down")

    task = send_listing_status_email

    await asyncio.to_thread(
        task.on_failure,
        exc=exc,
        task_id="fake-task-id",
        args=(listing.id, "agent"),
        kwargs={"entity_type": "listing"},
        einfo=None,
    )

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == str(listing.id))
    )
    log = result.scalar_one_or_none()

    assert log is not None
    assert log.action == "notification_failed"
    assert log.entity_type == "listing"
    assert log.triggered_by == "automation"
