import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User
from app.schemas.approval_queue import RejectRequest, ModifyRequest, ApprovalQueueRead
from app.services.approval_queue import (
    get_approval_entry,
    get_pending_for_agent,
    approve_entry,
    reject_entry,
    modify_and_approve,
)

router = APIRouter(prefix="/approval-queue", tags=["approval_queue"])


@router.get("/", response_model=list[ApprovalQueueRead])
async def list_pending_route(
    entity_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    # TODO: outline's get_pending_for_agent signature is (db, agent_id) only —
    # entity_type/status filtering isn't part of it. Either extend the service
    # signature or filter this result in the router. Don't leave these silently unused.
    pending = await get_pending_for_agent(db, current_user.id)
    return pending


@router.get("/{id}", response_class=ApprovalQueueRead)
async def get_entry_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    entry = await get_approval_entry(db, id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    # TODO: ownership check — same open question as list_pending_route:
    # what ties this entry to "this agent" if they're not admin?
    return entry


@router.post("/{id}/approve", response_model=ApprovalQueueRead)
async def approve_entry_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    # TODO: call approve_entry(db, id, reviewer_id=current_user.id)
    # TODO: 404 if entry missing, 409 if entry.status != "pending" (already resolved)
    pass


@router.post("/{id}/reject", response_model=ApprovalQueueRead)
async def reject_entry_route(
    id: uuid.UUID,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    # TODO: call reject_entry(db, id, reviewer_id=current_user.id, reason=payload.reason)
    # TODO: same 404/409 handling as approve
    pass


@router.post("/{id}/modify", response_model=ApprovalQueueRead)
async def modify_entry_route(
    id: uuid.UUID,
    payload: ModifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    entry = await modify_and_approve(
        db, id, reviewer_id=current_user.id, modified_context=payload.modified_context
    )
    if not entry:
        raise HTTPException(404, "Entry not found")
    return entry
