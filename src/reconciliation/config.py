from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "reconciliation"

    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-haiku-4-5-20251001"


settings = Settings()