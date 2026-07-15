import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader
from app.automation.hooks import fire_hook
from app.core.config import settings
from app.core.state_machine import DOCUMENT_MACHINE
from app.models.audit_log import AuditLog
from app.models.approval_queue import ApprovalQueue
from app.models.document import Documents
from app.models.listing import Listings
from app.models.contact import Contacts
from app.models.user import Users


async def _user_can_access_document(db: AsyncSession, document, current_user: Users):
    if current_user.role == "admin":
        return True
    if document.created_by_id == current_user.id:
        return True

    listing_result = await db.execute(
        select(Listings).where(Listings.id == document.listing_id)
    )

    listing = listing_result.scalar_one_or_none()
    if listing and listing.agent_id == current_user.id:
        return True

    contact_result = await db.execute(
        select(Contacts).where(Contacts.id == document.contact_id)
    )
    contact = contact_result.scalar_one_or_none()
    if contact and (
        contact.agent_id == current_user.id or contact.user_id == current_user.id
    ):
        return True

    return False


async def _generate_and_queue_document(
    db,
    template_name,
    doc_type,
    listing,
    contact,
    pipeline,
    agent,
    created_by_id,
    generated_by="automation",
):

    generated_at = datetime.now(timezone.utc)

    document = await create_document_record(
        db=db,
        listing_id=listing.id,
        contact_id=contact.id if contact else None,
        pipeline_id=pipeline.id if pipeline else None,
        created_by_id=created_by_id,
        type=doc_type,
        file_path="",
        generated_by=generated_by,
    )

    template_context = {
        "listing": listing,
        "contact": contact,
        "agent": agent,
        "document_id": document.id,
        "generated_at": generated_at,
        "pipeline": pipeline,
    }

    html = await render_template(template_name, template_context)
    pdf_bytes = await generate_pdf(html)
    filename = f"{uuid.uuid4()}.pdf"
    file_path = await save_pdf_to_disk(pdf_bytes, filename)

    await update_file_path(db, document.id, file_path)

    queue_entry = ApprovalQueue(
        entity_type="document",
        entity_id=str(document.id),
        proposed_action="send_document",
        proposed_state="sent",
        context={
            "document_id": str(document.id),
            "listing_id": str(listing.id),
            "pipeline_id": str(pipeline.id) if pipeline else None,
            "contact_id": str(contact.id) if contact else None,
        },
        status="pending",
        created_by="automation",
    )
    db.add(queue_entry)

    await db.commit()

    return document


async def _check_document_access(db: AsyncSession, document, current_user: Users):
    """Single document check. Raises 403 if document not accessible"""
    if not await _user_can_access_document(db, document, current_user):
        raise HTTPException(403, "Not authorized to access this document")


async def _filter_accessible_documents(
    db: AsyncSession, documents: list, current_user: Users
):
    """List check. Returns only the documents the user can access"""
    return [
        doc
        for doc in documents
        if await _user_can_access_document(db, doc, current_user)
    ]


async def render_template(type: str, context: dict):
    file_name = f"{type}.html"

    env = Environment(loader=FileSystemLoader("app/templates/"))

    template = env.get_template(file_name)
    html = template.render(**context)

    return html


async def generate_pdf(html: str):
    from weasyprint import HTML

    pdf = HTML(string=html)
    return pdf.write_pdf()


async def save_pdf_to_disk(pdf_bytes: bytes, filename: str):
    import os

    docs_dir = settings.generated_docs_dir

    file_path = os.path.join(docs_dir, filename)

    os.makedirs(docs_dir, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    return file_path


async def create_document_record(
    db: AsyncSession,
    listing_id: uuid.UUID,
    contact_id: uuid.UUID | None,
    pipeline_id: uuid.UUID | None,
    created_by_id: uuid.UUID,
    type: str,
    file_path: str,
    generated_by: str,
):
    document = Documents(
        id=uuid.uuid4(),
        listing_id=listing_id,
        contact_id=contact_id,
        pipeline_id=pipeline_id,
        created_by_id=created_by_id,
        type=type,
        file_path=file_path,
        generated_by=generated_by,
        status="draft",
    )
    db.add(document)

    await db.commit()
    await db.refresh(document)

    return document


async def get_document(db: AsyncSession, document_id: uuid.UUID):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    return result.scalar_one_or_none()


async def list_documents(db: AsyncSession, **filters):
    query = select(Documents)

    for k, v in filters.items():
        if v is not None:
            query = query.where(getattr(Documents, k) == v)

    result = await db.execute(query)

    return result.scalars().all()


async def update_status(
    db: AsyncSession,
    id: uuid.UUID,
    new_status: str,
    actor_id: uuid.UUID,
    triggered_by="manual",
):
    result = await db.execute(select(Documents).where(Documents.id == id))
    document = result.scalar_one_or_none()

    if document is None:
        return

    from_status = document.status
    to_status = new_status

    transition = DOCUMENT_MACHINE.get_transition(from_status, to_status)
    if transition is None:
        raise HTTPException(400, f"Unable to transition {from_status} to {to_status}")

    context = {
        "document_id": str(document.id),
        "from_status": from_status,
        "to_status": to_status,
    }

    if transition.requires_approval:
        queue_entry = ApprovalQueue(
            entity_type="document",
            entity_id=str(document.id),
            proposed_action="status_change",
            proposed_state=to_status,
            context=context,
            status="pending",
            created_by="system" if triggered_by == "manual" else "automation",
        )
        db.add(queue_entry)
        await db.commit()
        await db.refresh(queue_entry)
        return queue_entry

    document.status = new_status

    log = AuditLog(
        entity_type="document",
        entity_id=str(document.id),
        actor_id=actor_id,
        action="status_change",
        from_state=from_status,
        to_state=to_status,
        triggered_by=triggered_by,
    )
    db.add(log)

    await db.commit()
    await db.refresh(document)

    if transition.automation_hook:
        await fire_hook(transition.automation_hook, context)

    return document


async def update_file_path(db: AsyncSession, document_id: uuid.UUID, file_path: str):
    result = await db.execute(select(Documents).where(Documents.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        return
    document.file_path = file_path

    await db.commit()
    await db.refresh(document)

    return document
