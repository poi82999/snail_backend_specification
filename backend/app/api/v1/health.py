from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core import database
from app.core.redis import get_redis

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_status = "down"
    redis_status = "down"

    sessionmaker = database._sessionmaker
    if sessionmaker is not None:
        try:
            async with sessionmaker() as session:
                await session.execute(text("SELECT 1"))
            db_status = "up"
        except Exception:
            db_status = "down"

    try:
        await get_redis().ping()
        redis_status = "up"
    except Exception:
        redis_status = "down"

    return HealthResponse(
        status="ok" if db_status == "up" and redis_status == "up" else "degraded",
        db=db_status,
        redis=redis_status,
    )
