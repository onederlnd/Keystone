import uuid
from datetime import datetime
from pydantic import BaseModel


class ListingCreate(BaseModel):
    agent_id: uuid.UUID
    seller_id: uuid.UUID
    address: str
    city: str
    state: str
    zip: str
    price: int
    bedrooms: int
    bathrooms: int
    sqft: int
    mls_id: str
    description: str | None = None


class ListingRead(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    seller_id: uuid.UUID
    address: str
    city: str
    state: str
    price: int
    status: str
    bedrooms: int
    bathrooms: int
    sqft: int
    mls_id: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class ListingUpdate(BaseModel):
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    price: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    sqft: int | None = None
    description: str | None = None
    mls_id: str | None = None


class ListingStatusUpdate(BaseModel):
    new_status: str
    changed_by_id: uuid.UUID
    notes: str | None = None
    triggered_by: str


class ListingStatusHistoryRead(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    previous_status: str
    new_status: str
    changed_by_id: uuid.UUID
    notes: str | None = None
    triggered_by: str
    created_at: datetime


class ListingFilterParams(BaseModel):
    city: str | None = None
    state: str | None = None
    status: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
