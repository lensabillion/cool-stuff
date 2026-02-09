import os
import json
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


def parse_cors_origins(value: str | None) -> List[str]:
    """
    Accepts:
      - JSON list string: '["https://a.com","http://localhost:3000"]'
      - Comma-separated:  'https://a.com,http://localhost:3000'
    """
    if not value:
        return []
    value = value.strip()
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings(BaseSettings):
    # Mongo
    MONGO_URI: str = Field(default="mongodb://localhost:27017")
    MONGO_AUTH_DB: str = Field(default="auth_db")
    MONGO_APP_DB: str = Field(default="app_db")

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379")

    # JWT
    JWT_SECRET: str = Field(default="change-me")
    JWT_ALG: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRES_MIN: int = Field(default=60)

    # CORS
    # Default allows local Next.js + your Lovable domain
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://cosas-cool.lovable.app",
    ])

    class Config:
        env_file = ".env"
        extra = "ignore"


# Create settings object
settings = Settings()

# If CORS_ORIGINS is provided via env, parse it (JSON or comma-separated)
cors_env = os.getenv("CORS_ORIGINS")
if cors_env:
    settings.CORS_ORIGINS = parse_cors_origins(cors_env)
