import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.approval_queue import ApprovalQueue
from app.models.override_log import OverrideLog

# TODO: from app.models.override_log import OverrideLog
from app.automation.hooks import fire_hook


async def get_pending_for_agent(db: AsyncSession, agent_id: uuid.UUID):
    result = await db.execute(select(ApprovalQueue).where(status="pending"))

    # TODO: outline doesn't say how "belongs to this agent" is determined —
    #       ApprovalQueue has no agent_id column. Options:
    #         a) join through entity_type/entity_id to the underlying listing/pipeline/document's agent
    #         b) admins see all, agents see none until that join exists
    #       decide before writing the query
    # TODO: entity_type / status filters from the router aren't in this signature yet —
    #       outline's signature is (db, agent_id) only. Either add params here,
    #       or filter in the router after this returns. Pick one, keep it consistent.4ew


async def get_approval_entry(db: AsyncSession, id: uuid.UUID):
    # NOTE: not listed in outline's 7.2 checklist — router's GET /{id} needs
    # something like this though. Confirm you want it named this way before
    # I treat it as settled.
    # TODO: db.get(ApprovalQueue, id), return None if missing
    pass


async def approve_entry(db: AsyncSession, id: uuid.UUID, reviewer_id: uuid.UUID):
    # TODO: fetch entry, 404-equivalent (return None) if missing
    # TODO: guard — only proceed if entry.status == "pending" (else return None/raise)
    # TODO: apply the queued action — this is the part the outline is vague on:
    #       proposed_action + proposed_state + context need to translate into
    #       an actual state transition on the target entity (listing/pipeline/document).
    #       Likely needs a dispatch table keyed by entity_type.
    # TODO: set entry.status = "approved", reviewed_by_id = reviewer_id, reviewed_at = now
    # TODO: write override_log — action="approved", original_context=entry.context,
    #       final_context=entry.context (unchanged for a plain approve)
    # TODO: "triggers downstream hooks" per outline — call fire_hook() after the
    #       state change actually applies, same as every other transition
    pass


async def reject_entry(
    db: AsyncSession, id: uuid.UUID, reviewer_id: uuid.UUID, reason: str
):
    # TODO: fetch entry, guard on status == "pending"
    # TODO: set status = "rejected", reviewed_by_id, reviewed_at
    # TODO: no state change applied to the underlying entity — reject just closes the queue entry
    # TODO: write override_log — action="rejected", reason=reason,
    #       original_context=entry.context, final_context=None (nothing was applied)
    pass


async def modify_and_approve(
    db: AsyncSession, id: uuid.UUID, reviewer_id: uuid.UUID, modified_context: dict
):
    # TODO: fetch entry, guard on status == "pending"
    # TODO: open decision from before — does modified_context overwrite entry.context,
    #       or does entry.context stay as the original proposal and only override_log
    #       carries the diff? Outline's override_log has both original_context and
    #       final_context, which suggests entry.context can stay untouched — but confirm.
    # TODO: apply the *modified* context, not the original, using the same dispatch
    #       logic as approve_entry
    # TODO: set status = "approved" (modify-then-approve, not a separate status value —
    #       outline's ApprovalQueue.status enum only has pending/approved/rejected/expired)
    # TODO: reviewed_by_id, reviewed_at
    # TODO: write override_log — action="modified", original_context=<the original>,
    #       final_context=modified_context, reason=None or optional
    # TODO: fire_hook after applying, same as approve_entry
    pass


async def expire_stale_entries(db: AsyncSession):
    # TODO: query ApprovalQueue where status == "pending" and expires_at < now
    # TODO: bulk-update status = "expired"
    # TODO: outline says this is also a Celery periodic task — this function is just
    #       the DB logic; wrap it in app/tasks/ separately (not yet in outline —
    #       worth adding a checkbox under 7.2 or 7.x for the task file itself)
    pass
