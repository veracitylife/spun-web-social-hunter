from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="postgresql+asyncpg://social_hunter:local_dev_only_change_me@postgres:5432/social_hunter")
    redis_url: str = Field(default="redis://redis:6379/0")
    api_cors_origins: str = Field(default="http://localhost:5173")
    hibp_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    ipinfo_token_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    hunter_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    people_data_labs_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    twilio_account_sid_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    twilio_auth_token_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    github_token_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    reddit_client_id_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    reddit_client_secret_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    x_bearer_token_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    brave_search_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    serpapi_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    bing_search_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    tavily_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    exa_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    google_places_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    yelp_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    securitytrails_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    builtwith_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    wappalyzer_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    dnsdb_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    fullcontact_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")
    external_engine_api_key_ref: str = Field(default="REPLACE_WITH_VAULT_REFERENCE")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
