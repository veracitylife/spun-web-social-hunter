"""Vault credential injection service for external API keys and secrets."""
import os
from typing import Optional

from pydantic import BaseModel, Field


class VaultConfig(BaseModel):
    """HashiCorp Vault configuration."""
    vault_addr: str = Field(default_factory=lambda: os.getenv("VAULT_ADDR", "http://localhost:8200"))
    vault_token: Optional[str] = Field(default_factory=lambda: os.getenv("VAULT_TOKEN"))
    vault_namespace: Optional[str] = Field(default_factory=lambda: os.getenv("VAULT_NAMESPACE"))
    vault_enabled: bool = Field(default_factory=lambda: os.getenv("VAULT_ENABLED", "false").lower() == "true")
    secrets_path: str = "secret/data/social-hunter"  # KV v2 path


class VaultService:
    """Manages credential injection from HashiCorp Vault or environment fallback."""

    def __init__(self, config: VaultConfig):
        self.config = config
        self.cache: dict[str, str] = {}  # In-memory cache (demo)

    async def get_secret(self, secret_key: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Vault or environment variable.
        Priority: Vault > environment variable > None
        """
        # Check cache
        if secret_key in self.cache:
            return self.cache[secret_key]

        # Try Vault
        if self.config.vault_enabled:
            secret = await self._vault_get(secret_key)
            if secret:
                self.cache[secret_key] = secret
                return secret

        # Fall back to environment variable
        if fallback_env_var:
            secret = os.getenv(fallback_env_var)
            if secret and not secret.startswith("REPLACE_WITH_"):
                self.cache[secret_key] = secret
                return secret

        return None

    async def _vault_get(self, secret_key: str) -> Optional[str]:
        """
        Fetch a secret from HashiCorp Vault KV v2.
        Placeholder for future integration.
        """
        # TODO: Implement Vault API client
        # Example: POST /v1/secret/data/social-hunter with secret_key
        # import hvac
        # client = hvac.Client(url=self.config.vault_addr, token=self.config.vault_token)
        # response = client.secrets.kv.v2.read_secret_version(path=self.config.secrets_path)
        # return response['data']['data'].get(secret_key)
        return None

    async def get_hibp_api_key(self) -> Optional[str]:
        """Get Have I Been Pwned API key."""
        return await self.get_secret("hibp_api_key", "HIBP_API_KEY")

    async def get_ipinfo_token(self) -> Optional[str]:
        """Get IPinfo.io API token."""
        return await self.get_secret("ipinfo_token", "IPINFO_TOKEN")

    async def get_hunter_api_key(self) -> Optional[str]:
        """Get Hunter.io API key."""
        return await self.get_secret("hunter_api_key", "HUNTER_API_KEY")

    async def rotate_secret(self, secret_key: str, new_value: str) -> bool:
        """
        Rotate a secret in Vault.
        Placeholder for future integration.
        """
        # TODO: Implement secret rotation
        # Update both Vault and environment cache
        self.cache[secret_key] = new_value
        return True
