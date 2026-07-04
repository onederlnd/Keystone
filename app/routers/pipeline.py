import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.pipeline import (
    add_to_pipeline,
    list_pipeline,
    get_pipeline_entry,
    remove_pipeline_entry,
    update_pipeline_entry,
)
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineRead,
    PipelineUpdate,
    PipelineFilterParams,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/", response_model=PipelineRead)
async def add_to_pipeline_route(
    data: PipelineCreate, db: AsyncSession = Depends(get_db)
):
    return await add_to_pipeline(db, data)


@router.get("/", response_model=list[PipelineRead])
async def list_pipeline_route(
    filters: PipelineFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await list_pipeline(db, filters)


@router.get("/{pipeline_id}", response_model=PipelineRead)
async def get_pipeline_entry_route(
    pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    pipeline = await get_pipeline_entry(db, pipeline_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    return pipeline


@router.patch("/{pipeline_id}", response_model=PipelineRead)
async def update_pipeline_entry_route(
    pipeline_id: uuid.UUID, data: PipelineUpdate, db: AsyncSession = Depends(get_db)
):
    pipeline = await update_pipeline_entry(db, pipeline_id, data)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    return pipeline


@router.patch("/{pipeline_id}/remove", response_model=PipelineRead)
async def remove_pipeline_entry_route(
    pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    pipeline = await remove_pipeline_entry(db, pipeline_id)
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")

    return pipeline
