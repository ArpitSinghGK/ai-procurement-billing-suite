"""Central configuration, loaded from environment / ``.env``.

All endpoints and secrets are injected — nothing is hardcoded. See
``.env.example`` for the full set of variables.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = "sk-ant-not-set"
    llm_model: str = "claude-opus-4-8"

    # ERP
    erp_base_url: str = "https://erp.example.com/api/v1"
    erp_api_key: str = "erp-not-set"

    # WhatsApp
    whatsapp_api_base: str = "https://graph.facebook.com/v21.0"
    whatsapp_phone_number_id: str = "000000000000000"
    whatsapp_access_token: str = "whatsapp-not-set"

    # Email
    email_imap_host: str = "imap.example.com"
    email_smtp_host: str = "smtp.example.com"
    email_username: str = "sales@example.com"
    email_password: str = "change-me"

    # Commercial
    default_markup_pct: float = 0.18


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (one read per process)."""
    return Settings()
