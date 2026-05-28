from pydantic import BaseModel


class FollowToggleResponse(BaseModel):
    followed: bool
    follower_count: int
