from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AiAnalysisStatus,
    DesignOptionKind,
    JobStatus,
    LlmJobType,
    Visibility,
)


class DesignOptionCreate(BaseModel):
    kind: DesignOptionKind = Field(
        description="디자인 옵션 종류. 허용값: extend, removal, care.",
        examples=["extend"],
    )
    name: str = Field(min_length=1, max_length=80)
    price_delta: int = Field(default=0, ge=0)
    duration_delta_min: int = Field(default=0, ge=0, le=600)
    sort_order: int = 0


class DesignOptionUpdate(BaseModel):
    kind: DesignOptionKind | None = Field(
        default=None,
        description="디자인 옵션 종류. 허용값: extend, removal, care.",
        examples=["care"],
    )
    name: str | None = Field(default=None, min_length=1, max_length=80)
    price_delta: int | None = Field(default=None, ge=0)
    duration_delta_min: int | None = Field(default=None, ge=0, le=600)
    sort_order: int | None = None
    is_active: bool | None = None


class DesignOptionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: DesignOptionKind = Field(
        description="디자인 옵션 종류. 허용값: extend, removal, care.",
        examples=["removal"],
    )
    name: str
    price_delta: int
    duration_delta_min: int
    sort_order: int
    is_active: bool


class DesignCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    base_price: int = Field(ge=0)
    duration_minutes: int = Field(ge=30, le=600)
    designer_ids: list[UUID] = Field(min_length=1)
    image_upload_keys: list[str] = Field(min_length=1, max_length=10)
    owner_tags: list[str] = Field(default_factory=list)


class DesignUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    base_price: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=30, le=600)
    designer_ids: list[UUID] | None = Field(default=None, min_length=1)
    image_upload_keys: list[str] | None = Field(default=None, min_length=1, max_length=10)
    owner_tags: list[str] | None = None


class DesignVisibilityUpdate(BaseModel):
    visibility: Visibility


class DesignReanalyzeQueued(BaseModel):
    design_id: UUID
    queued_at: datetime


class DesignImagePublic(BaseModel):
    id: UUID
    original_url: str
    processed_url: str | None = None
    sort_order: int
    is_thumbnail: bool


class DesignDesignerPublic(BaseModel):
    id: UUID
    shop_id: UUID
    name: str
    position: str | None = None
    profile_image_url: str | None = None
    specialty_tags: list[str]


class LlmJobSummary(BaseModel):
    id: UUID
    job_type: LlmJobType
    status: JobStatus
    attempts: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class DesignMe(BaseModel):
    id: UUID
    shop_id: UUID
    title: str
    description: str | None = None
    base_price: int
    duration_minutes: int
    thumbnail_url: str | None = None
    visibility: Visibility
    ai_analysis_status: AiAnalysisStatus
    owner_tags: list[str]
    ai_tags: list[str]
    color_palette: list[str]
    style_category: str | None = None
    nail_shape: str | None = None
    ai_confidence: Decimal | None = None
    ai_error_code: str | None = None
    ai_error_message: str | None = None
    ai_model_version: str | None = None
    search_indexed_at: datetime | None = None
    images: list[DesignImagePublic] = Field(default_factory=list)
    designers: list[DesignDesignerPublic] = Field(default_factory=list)
    options: list[DesignOptionPublic] = Field(default_factory=list)
    llm_jobs: list[LlmJobSummary] = Field(default_factory=list, max_length=1)
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DesignShopSummary(BaseModel):
    id: UUID
    name: str
    region: str | None = None
    thumbnail_url: str | None = None


class DesignPublic(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    base_price: int
    duration_minutes: int
    thumbnail_url: str | None = None
    images: list[DesignImagePublic] = Field(default_factory=list)
    ai_tags: list[str]
    color_palette: list[str]
    style_category: str | None = None
    nail_shape: str | None = None
    shop: DesignShopSummary
    designers: list[DesignDesignerPublic] = Field(default_factory=list)
    options: list[DesignOptionPublic] = Field(default_factory=list)
    average_rating: float
    favorite_count: int
    favorited_by_me: bool
    score: float | None = None
    created_at: datetime
