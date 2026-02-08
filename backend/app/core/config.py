from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_auth_db: str = "auth_db"
    mongo_app_db: str = "app_db"

    jwt_secret: str = "change-me"
    jwt_alg: str = "HS256"
    access_token_expires_min: int = 60

    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

settings = Settings()
