from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DesignerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=80)
    career_years: int | None = Field(default=None, ge=0)
    profile_image_object_key: str | None = Field(default=None, min_length=1)
    specialty_tags: list[str] = Field(default_factory=list)


class DesignerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=80)
    career_years: int | None = Field(default=None, ge=0)
    profile_image_object_key: str | None = Field(default=None, min_length=1)
    specialty_tags: list[str] | None = None


class DesignerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shop_id: UUID
    name: str
    position: str | None = None
    career_years: int | None = None
    profile_image_url: str | None = None
    specialty_tags: list[str]
    is_active: bool


class ScheduleEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int = Field(ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    break_start_time: time | None = None
    break_end_time: time | None = None
    is_day_off: bool = False


class DesignerScheduleSet(BaseModel):
    entries: list[ScheduleEntry] = Field(default_factory=list, max_length=7)


class TimeOffCreate(BaseModel):
    off_date: date
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None


class TimeOffPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    off_date: date
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None
