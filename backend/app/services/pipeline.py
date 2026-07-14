import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.automation.hooks import fire_hook
from backend.app.models.pipeline import Pipelines
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.pipeline import (
    PipelineCreate,
    PipelineFilterParams,
    PipelineUpdate,
)
from backend.app.core.state_machine import PIPELINE_MACHINE
from backend.app.models.approval_queue import ApprovalQueue


async def add_to_pipeline(db: AsyncSession, data: PipelineCreate):
    pipeline = Pipelines(**data.model_dump())
    db.add(pipeline)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Pipeline already exists")

    await db.refresh(pipeline)

    log = AuditLog(
        entity_type="pipeline",
        entity_id=str(pipeline.id),
        action="added",
        triggered_by="automatic",
    )
    db.add(log)

    await db.commit()

    return pipeline


async def get_pipeline_entry(db: AsyncSession, pipeline_id: uuid.UUID):
    result = await db.execute(select(Pipelines).where(Pipelines.id == pipeline_id))
    return result.scalar_one_or_none()


async def list_pipeline(db: AsyncSession, data: PipelineFilterParams):
    query = select(Pipelines)
    model = data.model_dump(exclude_unset=True)

    for k, v in model.items():
        if v is not None:
            query = query.where(getattr(Pipelines, k) == v)

    result = await db.execute(query)

    pipeline = result.scalars().all()

    return pipeline


async def remove_pipeline_entry(db: AsyncSession, pipeline_id: uuid.UUID):
    result = await db.execute(select(Pipelines).where(Pipelines.id == pipeline_id))
    pipeline = result.scalar_one_or_none()

    if pipeline is None:
        return

    log = AuditLog(
        entity_type="pipeline",
        entity_id=str(pipeline.id),
        action="removed",
        triggered_by="manual",
        actor_id=None,
    )
    db.add(log)

    await db.delete(pipeline)
    await db.commit()

    return pipeline


async def update_pipeline_entry(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    data: PipelineUpdate,
    triggered_by="manual",
):
    result = await db.execute(select(Pipelines).where(Pipelines.id == pipeline_id))
    entry = result.scalar_one_or_none()

    if entry is None:
        return

    from_stage = entry.stage
    to_stage = data.stage

    transition = PIPELINE_MACHINE.get_transition(from_stage, to_stage)
    if transition is None:
        raise HTTPException(400, f"Cannot transition from {from_stage} to {to_stage}")

    model = data.model_dump(exclude_unset=True)
    model.pop("stage", None)

    for k, v in model.items():
        setattr(entry, k, v)

    if transition.requires_approval:
        approval = ApprovalQueue(
            entity_type="pipeline",
            entity_id=str(entry.id),
            proposed_action="stage_change",
            proposed_state=to_stage,
            context={"from_stage": from_stage, "to_stage": to_stage},
            created_by=triggered_by,
        )
        db.add(approval)

        await db.commit()
        await db.refresh(entry)

        return entry

    entry.stage = to_stage
    entry.last_stage_change_at = datetime.now(timezone.utc).replace(tzinfo=None)

    log = AuditLog(
        entity_type="pipeline",
        entity_id=str(entry.id),
        action="stage_change",
        triggered_by=triggered_by,
    )
    db.add(log)

    await db.commit()
    await db.refresh(entry)

    context = {
        "pipeline_id": str(entry.id),
        "from_stage": from_stage,
        "to_stage": to_stage,
    }
    await fire_hook(transition.automation_hook, context)

    return entry


async def get_stale_pipeline_entries(db: AsyncSession, days_threshold: int):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).replace(
        tzinfo=None
    )

    result = await db.execute(
        select(Pipelines).where(Pipelines.last_stage_change_at <= cutoff)
    )

    return result.scalars().all()
