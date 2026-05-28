from app.core.config import Settings


def test_settings_loads_minimum() -> None:
    s = Settings(
        DATABASE_URL="postgresql+asyncpg://u:p@localhost:5432/d",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="x" * 32,
    )
    assert s.ENV == "local"
    assert s.is_prod is False
    assert s.JWT_ALGORITHM == "HS256"
