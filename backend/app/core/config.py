import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Mongo
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_AUTH_DB: str = os.getenv("MONGO_AUTH_DB", "auth_db")
    MONGO_APP_DB: str = os.getenv("MONGO_APP_DB", "app_db")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "60"))

settings = Settings()
