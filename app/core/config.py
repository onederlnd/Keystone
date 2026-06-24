# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    environment: str = "development"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    REDIS_URL: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    debug: bool = True
