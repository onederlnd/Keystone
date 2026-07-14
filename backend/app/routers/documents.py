import os
import uuid
from typing import Union
from jinja2 import TemplateNotFound
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.document import (
    get_document,
    list_documents,
    update_status,
    _check_document_access,
    _filter_accessible_documents,
)
from backend.app.schemas.document import (
    DocumentGenerateRequest,
    DocumentRead,
    DocumentStatusUpdate,
    DocumentFilterParams,
)
from backend.app.models.user import Users
from backend.app.models.contact import Contacts
from backend.app.models.listing import Listings
from backend.app.models.pipeline import Pipelines
from backend.app.schemas.approval_queue import ApprovalQueueRead
from backend.app.services.document import _generate_and_queue_document
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead)
async def generate_document(
    data: DocumentGenerateRequest,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing_result = await db.execute(
        select(Listings).where(Listings.id == data.listing_id)
    )
    listing = listing_result.scalar_one_or_none()

    if listing is None:
        raise HTTPException(404, "Listing not found")

    contact_result = await db.execute(
        select(Contacts).where(Contacts.id == data.contact_id)
    )
    contact = contact_result.scalar_one_or_none()

    pipeline_result = await db.execute(
        select(Pipelines).where(Pipelines.id == data.pipeline_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()

    agent_result = await db.execute(select(Users).where(Users.id == listing.agent_id))
    agent = agent_result.scalar_one_or_none()

    try:
        document = await _generate_and_queue_document(
            db,
            template_name=data.type,
            doc_type=data.type,
            listing=listing,
            contact=contact,
            pipeline=pipeline,
            agent=agent,
            created_by_id=current_user.id,
            generated_by="manual",
        )
    except TemplateNotFound:
        raise HTTPException(400, f"Unknown document type: {data.type}")

    return document


@router.get("/", response_model=list[DocumentRead])
async def list_documents_route(
    current_user: Users = Depends(get_current_user),
    filters: DocumentFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):

    documents = await list_documents(db, **filters.model_dump(exclude_none=True))
    return await _filter_accessible_documents(db, documents, current_user)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document_route(
    document_id: uuid.UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(404, "Document not found")

    await _check_document_access(db, document, current_user)

    return document


@router.get("/{document_id}/download")
async def download_document_route(
    document_id: uuid.UUID,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(404, "Document not found")

    await _check_document_access(db, document, current_user)

    if not os.path.exists(document.file_path):
        raise HTTPException(404, "Document file not found on disk")

    return FileResponse(
        path=document.file_path,
        media_type="application/pdf",
        filename=os.path.basename(document.file_path),
    )


@router.post(
    "/{document_id}/status", response_model=Union[DocumentRead, ApprovalQueueRead]
)
async def update_document_status_route(
    document_id: uuid.UUID,
    payload: DocumentStatusUpdate,
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await update_status(
        db,
        document_id,
        payload.new_status,
        actor_id=current_user.id,
        triggered_by="manual",
    )

    if result is None:
        raise HTTPException(404, "Document not found")

    await _check_document_access(db, result, current_user)

    return result
