from pydantic import BaseModel


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int


class SaveToggleResponse(BaseModel):
    saved: bool
    save_count: int
