from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DSYSTEM SERVER CORE"
    app_version: str = "1.0.1.7"
    environment: str = "development"
    secret_key: str = "troque-esta-chave-em-producao"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./dsystem_core.db"

    master_username: str = "master"
    master_password: str = "master123"
    master_full_name: str = "Master DSYSTEM"
    master_email: str = "master@dsystem.local"
    default_company_name: str = "DSYSTEM MASTER"
    default_company_slug: str = "dsystem-master"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
