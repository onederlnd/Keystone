import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    agent_id: uuid.UUID
    seller_id: uuid.UUID
    address: str = Field(max_length=255)
    city: str = Field(max_length=100)
    state: str = Field(max_length=50)
    zip: str = Field(max_length=10)
    price: int
    bedrooms: int
    bathrooms: int
    sqft: int
    mls_id: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=2000)


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
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=50)
    zip: str | None = Field(default=None, max_length=10)
    price: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    sqft: int | None = None
    description: str | None = Field(default=None, max_length=2000)
    mls_id: str | None = Field(default=None, max_length=50)


class ListingStatusUpdate(BaseModel):
    new_status: str
    changed_by_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=1000)
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
