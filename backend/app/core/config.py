from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# allow_credentials=True 환경에서는 "*" 대신 정확한 로컬 웹 origin을 명시한다.
# 네이티브 iOS/Android 네트워크 호출은 브라우저 CORS 적용 대상이 아니며,
# Expo/웹 미리보기처럼 브라우저 origin이 생기는 개발 경로만 여기에 추가한다.
LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:19006",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:19006",
    "http://127.0.0.1:8081",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENV: Literal["local", "staging", "prod"] = "local"
    APP_NAME: str = "snail-backend"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: list(LOCAL_CORS_ORIGINS))

    # 로컬 기본값에 ?ssl=disable — Windows 한글 경로(asyncpg cert 자동탐색 버그) 회피용.
    # prod 환경에서는 .env / Secret Manager로 덮어쓰기 (Cloud SQL Auth Proxy는 ssl=require).
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://snail:snail@localhost:5432/snail?ssl=disable"  # type: ignore[assignment]
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 2

    REDIS_URL: RedisDsn = "redis://localhost:6379/0"  # type: ignore[assignment]

    JWT_SECRET: str = Field(default="dev-only-change-me-32-chars-minimum", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MIN: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 30

    APPLE_TEAM_ID: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_KEY_ID: str = ""
    APPLE_PRIVATE_KEY_PATH: str = ""

    APNS_TEAM_ID: str = ""
    APNS_KEY_ID: str = ""
    APNS_PRIVATE_KEY_PATH: str = ""
    APNS_BUNDLE_ID: str = ""
    APNS_USE_SANDBOX: bool = True

    OPENAI_API_KEY: str = ""
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_REQUEST_TIMEOUT_SEC: int = 30
    OPENAI_MODEL_VISION: str = "gpt-4o-mini"
    OPENAI_MODEL_EMBEDDING: str = "text-embedding-3-small"
    OPENAI_MAX_CONCURRENT: int = 5

    GCP_PROJECT_ID: str = ""
    GCS_BUCKET_DESIGNS: str = ""
    GCS_PUBLIC_BASE_URL: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    KAKAO_SENDER_KEY: str = ""
    BIZPPURIO_USER_ID: str = ""
    BIZPPURIO_API_KEY: str = ""
    KAKAO_TEMPLATE_CODES_JSON: str = ""

    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    @model_validator(mode="after")
    def validate_prod_secrets(self) -> "Settings":
        if self.ENV == "prod" and self.JWT_SECRET.startswith("dev-only"):
            raise ValueError("JWT_SECRET must be changed in prod")
        return self

    @property
    def is_prod(self) -> bool:
        return self.ENV == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
