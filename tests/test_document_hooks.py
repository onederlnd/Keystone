# tests/test_document_hooks.py

from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import settings
from app.automation.hooks import fire_hook
from app.models.document import Documents
from app.models.approval_queue import ApprovalQueue
from app.services.document import update_status


@pytest_asyncio.fixture(autouse=True)
async def register_hooks_for_test(reset_hook_registry, monkeypatch):
    """
    reset_hook_registry (conftest, autouse) clears REGISTRY before/after every
    test. Hook modules only call register_hook() at import time, so we have to
    force them to re-run their top-level registration code after the clear —
    otherwise REGISTRY is empty and fire_hook() finds nothing to call.
    Reloading also re-runs `from app.core.database import AsyncSessionLocal`
    inside each hook module, which is what picks up the patched test session.
    """
    import sys
    import importlib
    from app.automation.registry import REGISTRY
    from tests.conftest import TestSessionLocal

    REGISTRY.clear()

    for name in (
        "app.automation.document_hooks",
        "app.automation.pipeline_hooks",
    ):
        if name in sys.modules:
            importlib.reload(sys.modules[name])
        else:
            importlib.import_module(name)

    monkeypatch.setattr(
        "app.automation.document_hooks.AsyncSessionLocal", TestSessionLocal
    )
    monkeypatch.setattr(
        "app.automation.pipeline_hooks.AsyncSessionLocal", TestSessionLocal
    )
    yield


def _mock_pdf_pipeline():
    return (
        patch(
            "app.services.document.render_template",
            return_value="<html></html>",
        ),
        patch("app.services.document.generate_pdf", return_value=b"%PDF-1.4 fake"),
        patch(
            "app.services.document.save_pdf_to_disk",
            return_value="/tmp/fake-hook-doc.pdf",
        ),
    )


@pytest.mark.asyncio
async def test_listing_active_hook_generates_listing_agreement(
    db_session, create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db()

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", True):
        await fire_hook("listing.active", {"listing_id": str(listing.id)})

    result = await db_session.execute(
        select(Documents).where(Documents.listing_id == listing.id)
    )
    document = result.scalar_one_or_none()

    assert document is not None
    assert document.type == "listing_agreement"
    assert document.generated_by == "automation"
    assert document.contact_id is None
    assert document.pipeline_id is None
    assert document.file_path == "/tmp/fake-hook-doc.pdf"


@pytest.mark.asyncio
async def test_listing_active_hook_queues_for_review(
    db_session, create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db()

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", True):
        await fire_hook("listing.active", {"listing_id": str(listing.id)})

    doc_result = await db_session.execute(
        select(Documents).where(Documents.listing_id == listing.id)
    )
    document = doc_result.scalar_one_or_none()

    queue_result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(document.id))
    )
    queue_entry = queue_result.scalar_one_or_none()

    assert queue_entry is not None
    assert queue_entry.entity_type == "document"
    assert queue_entry.proposed_action == "send_document"
    assert queue_entry.proposed_state == "sent"
    assert queue_entry.status == "pending"
    assert queue_entry.created_by == "automation"


@pytest.mark.asyncio
async def test_listing_active_hook_noop_when_automation_disabled(
    db_session, create_listing_in_db, patch_async_session_local
):
    listing = await create_listing_in_db()

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", False):
        await fire_hook("listing.active", {"listing_id": str(listing.id)})

    result = await db_session.execute(
        select(Documents).where(Documents.listing_id == listing.id)
    )
    assert result.scalar_one_or_none() is None


# ---- pipeline.offer_submitted -> offer_letter ----


@pytest.mark.asyncio
async def test_pipeline_offer_submitted_hook_generates_offer_letter(
    db_session, create_pipeline_in_db, patch_async_session_local
):
    pipeline = await create_pipeline_in_db(stage="offer_submitted")

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", True):
        await fire_hook("pipeline.offer_submitted", {"pipeline_id": str(pipeline.id)})

    result = await db_session.execute(
        select(Documents).where(Documents.pipeline_id == pipeline.id)
    )
    document = result.scalar_one_or_none()

    assert document is not None
    assert document.type == "offer_letter"
    assert document.listing_id == pipeline.listing_id
    assert document.contact_id == pipeline.contact_id
    assert document.generated_by == "automation"


@pytest.mark.asyncio
async def test_pipeline_offer_submitted_hook_queues_for_review(
    db_session, create_pipeline_in_db, patch_async_session_local
):
    pipeline = await create_pipeline_in_db(stage="offer_submitted")

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", True):
        await fire_hook("pipeline.offer_submitted", {"pipeline_id": str(pipeline.id)})

    doc_result = await db_session.execute(
        select(Documents).where(Documents.pipeline_id == pipeline.id)
    )
    document = doc_result.scalar_one_or_none()

    queue_result = await db_session.execute(
        select(ApprovalQueue).where(ApprovalQueue.entity_id == str(document.id))
    )
    queue_entry = queue_result.scalar_one_or_none()

    assert queue_entry is not None
    assert queue_entry.context["pipeline_id"] == str(pipeline.id)
    assert queue_entry.context["contact_id"] == str(pipeline.contact_id)


# ---- pipeline.closed -> closing_summary ----


@pytest.mark.asyncio
async def test_pipeline_closed_hook_generates_closing_summary(
    db_session, create_pipeline_in_db, patch_async_session_local
):
    pipeline = await create_pipeline_in_db(stage="closed")

    p1, p2, p3 = _mock_pdf_pipeline()
    with p1, p2, p3, patch.object(settings, "automation_enabled", True):
        await fire_hook("pipeline.closed", {"pipeline_id": str(pipeline.id)})

    result = await db_session.execute(
        select(Documents).where(Documents.pipeline_id == pipeline.id)
    )
    document = result.scalar_one_or_none()

    assert document is not None
    assert document.type == "closing_summary"


# ---- Approval -> sent transition ----


@pytest.mark.asyncio
async def test_approving_queued_document_transitions_it_to_sent(
    db_session, create_document_in_db
):
    """
    draft -> sent is a requires_approval transition, so update_status queues it
    rather than applying it directly — same rule as listings/pipeline. This
    confirms that behavior for documents specifically. The actual "approve and
    apply" step belongs to Phase 7's approval_service.approve_entry(), which
    doesn't exist yet.
    """
    document, owner = await create_document_in_db(status="draft")

    result = await update_status(
        db=db_session,
        id=document.id,
        new_status="sent",
        actor_id=owner.id,
        triggered_by="manual",
    )

    assert isinstance(result, ApprovalQueue)
    assert result.entity_type == "document"
    assert result.entity_id == str(document.id)
    assert result.proposed_state == "sent"
    assert result.status == "pending"
    assert result.created_by == "system"  # triggered_by="manual" maps to "system"

    doc_result = await db_session.execute(
        select(Documents).where(Documents.id == document.id)
    )
    refreshed = doc_result.scalar_one_or_none()
    assert refreshed.status == "draft"
