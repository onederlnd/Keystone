# app/routers/contacts.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.contact import (
    create_contact,
    get_contact,
    update_contact,
    archive_contact,
    list_contacts,
)
from app.schemas.contact import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
)
from app.models.user import Users

router = APIRouter(prefix="/contacts", tags=["contact"])


@router.post("/", response_model=ContactRead)
async def create_contact_route(data: ContactCreate, db: AsyncSession = Depends(get_db)):
    return await create_contact(db, data)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact_route(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    contact = await get_contact(db, contact_id, current_user)
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact


@router.get("/", response_model=list[ContactRead])
async def list_contacts_routes(
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    return await list_contacts(db, current_user, type)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact_route(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    current_user: Users = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await update_contact(db, contact_id, data, current_user)
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact


@router.patch("/{contact_id}/archive", response_model=ContactRead)
async def archive_contact_route(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    contact = await archive_contact(db, contact_id, current_user)
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact
