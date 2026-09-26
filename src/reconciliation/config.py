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
    # Scelta basata su reports/extraction_eval.json: stessa precisione di Sonnet a circa un terzo del costo
    anthropic_extraction_model: str = "claude-haiku-4-5-20251001"
    # L'agente ragiona su piu' passaggi e decide quali tool usare: modello piu' capace
    anthropic_agent_model: str = "claude-sonnet-5"


settings = Settings()