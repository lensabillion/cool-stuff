import os

from pydantic import BaseModel


class Settings(BaseModel):
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    auth_db_name: str = os.getenv("AUTH_DB_NAME", "auth_db")
    app_db_name: str = os.getenv("APP_DB_NAME", "app_db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", "120"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "backend/uploads")


settings = Settings()
