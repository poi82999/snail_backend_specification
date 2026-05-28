from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.designs import DesignPublic
from app.schemas.reviews import ReviewPublic
from app.schemas.shops import ShopPublic

SearchScope = Literal["designs", "shops", "reviews"]
SearchSort = Literal[
    "relevance",
    "popular",
    "latest",
    "price_asc",
    "price_desc",
    "rating",
    "distance",
]


class SearchQuery(BaseModel):
    q: str | None = None
    scope: SearchScope = "designs"
    region: str | None = None
    colors: list[str] | None = None
    moods: list[str] | None = None
    price_min: int | None = Field(default=None, ge=0)
    price_max: int | None = Field(default=None, ge=0)
    duration_max: int | None = Field(default=None, ge=1)
    sort: SearchSort | None = None
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=50)


class SearchResult(BaseModel):
    items: list[DesignPublic | ShopPublic | ReviewPublic]
    next_cursor: str | None = None
    recommendations: list[DesignPublic] = Field(default_factory=list)
