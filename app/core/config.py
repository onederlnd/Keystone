# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Config Settings
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # General settings
    environment: str = "development"
    database_url: str
    algorithm: str = "HS256"
    debug: bool = False

    # Keys
    secret_key: str

    # Documents
    generated_docs_dir: str

    # Tokens
    access_token_expire_minutes: int = 30
    redis_url: str = ""

    # Automation
    automation_enabled: bool = False

    # SMTP
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str

    # API
    api_title: str = "Keystone API"


settings = Settings()
