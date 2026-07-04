import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.hooks import fire_hook
from app.models.contact import Contact
from app.models.audit_log import AuditLog
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate


async def create_contact(db: AsyncSession, data: ContactCreate):
    contact = Contact(**data.model_dump())
    db.add(contact)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Contact already exists")

    await db.refresh(contact)

    context = {"contact_id": str(contact.id), "agent_id": str(contact.agent_id)}
    fire_hook("contact.created", context)

    log = AuditLog(
        entity_type="contact",
        entity_id=str(contact.id),
        action="created",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)
    await db.commit()

    return contact


async def get_contact(db: AsyncSession, contact_id: uuid.UUID, current_user):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return None

    if current_user.role != "admin" and contact.agent_id != current_user.id:
        raise HTTPException(403, "Not authorized to access this contact")

    return contact


async def update_contact(
    db: AsyncSession, contact_id: uuid.UUID, data: ContactUpdate, current_user
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return None

    if current_user.role != "admin" and contact.agent_id != current_user.id:
        raise HTTPException(403, "Not authorized to modify this contact")

    model = data.model_dump(exclude_unset=True)
    for k, v in model.items():
        setattr(contact, k, v)

    await db.commit()
    await db.refresh(contact)

    return contact


async def archive_contact(db: AsyncSession, contact_id: uuid.UUID, current_user):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()

    if not contact:
        return None

    if current_user.role != "admin" and contact.agent_id != current_user.id:
        raise HTTPException(403, "Not authorized to access this contact")

    log = AuditLog(
        entity_type="contact",
        entity_id=str(contact.id),
        action="archived",
        triggered_by="manual",
        actor_id=None,
    )

    db.add(log)

    contact.is_archived = True

    await db.commit()

    return contact


async def list_contacts(db: AsyncSession, current_user, type: str | None = None):
    query = select(Contact)

    if current_user.role != "admin":
        query = query.where(Contact.agent_id == current_user.id)

    if type is not None:
        query = query.where(Contact.type == type)

    result = await db.execute(query)

    return result.scalars().all()
