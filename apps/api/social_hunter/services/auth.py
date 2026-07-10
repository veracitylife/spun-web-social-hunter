"""Authentication service with pluggable identity provider support."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    """Authenticated user context."""
    user_id: str
    email: str
    name: str
    plan_id: str = "free"
    roles: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    email: str
    name: str
    plan_id: str
    roles: list[str] = Field(default_factory=list)
    exp: datetime
    iat: datetime


class AuthConfig(BaseModel):
    """Authentication configuration."""
    jwt_secret: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret-key-change-in-production"))
    jwt_algorithm: str = "HS256"
    token_expiry_minutes: int = 1440  # 24 hours
    refresh_token_expiry_days: int = 30
    identity_provider: str = Field(default_factory=lambda: os.getenv("IDENTITY_PROVIDER", "mock"))  # mock, auth0, okta, oidc
    auth0_domain: Optional[str] = Field(default_factory=lambda: os.getenv("AUTH0_DOMAIN"))
    auth0_client_id: Optional[str] = Field(default_factory=lambda: os.getenv("AUTH0_CLIENT_ID"))
    okta_domain: Optional[str] = Field(default_factory=lambda: os.getenv("OKTA_DOMAIN"))
    oidc_issuer: Optional[str] = Field(default_factory=lambda: os.getenv("OIDC_ISSUER"))


class AuthService:
    """Manages authentication, token generation, and identity provider integration."""

    def __init__(self, config: AuthConfig):
        self.config = config

    def create_token(self, user: AuthUser, expires_in_minutes: Optional[int] = None) -> str:
        """Generate a JWT token for an authenticated user."""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=expires_in_minutes or self.config.token_expiry_minutes)
        payload = TokenPayload(
            sub=user.user_id,
            email=user.email,
            name=user.name,
            plan_id=user.plan_id,
            roles=user.roles,
            exp=expiry,
            iat=now,
        )
        token = jwt.encode(
            payload.model_dump(mode="json"),
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm,
        )
        return token

    def verify_token(self, token: str) -> Optional[AuthUser]:
        """Verify a JWT token and return the authenticated user context."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
            )
            return AuthUser(
                user_id=payload["sub"],
                email=payload["email"],
                name=payload["name"],
                plan_id=payload.get("plan_id", "free"),
                roles=payload.get("roles", []),
            )
        except jwt.InvalidTokenError:
            return None

    async def authenticate_with_provider(self, provider_token: str) -> Optional[AuthUser]:
        """Authenticate a user via external identity provider (Auth0, Okta, OIDC)."""
        if self.config.identity_provider == "mock":
            # Demo mode: always returns a demo user
            return AuthUser(
                user_id="demo-user-001",
                email="analyst@demo.local",
                name="Demo Analyst",
                plan_id="professional",
                roles=["analyst", "admin"],
            )
        elif self.config.identity_provider == "auth0":
            return await self._auth0_verify(provider_token)
        elif self.config.identity_provider == "okta":
            return await self._okta_verify(provider_token)
        elif self.config.identity_provider == "oidc":
            return await self._oidc_verify(provider_token)
        return None

    async def _auth0_verify(self, token: str) -> Optional[AuthUser]:
        """Verify token with Auth0. Placeholder for future integration."""
        # TODO: Implement Auth0 token verification using auth0-python
        # Example: verify token against Auth0 domain + client_id
        return None

    async def _okta_verify(self, token: str) -> Optional[AuthUser]:
        """Verify token with Okta. Placeholder for future integration."""
        # TODO: Implement Okta token verification
        return None

    async def _oidc_verify(self, token: str) -> Optional[AuthUser]:
        """Verify token with OIDC provider. Placeholder for future integration."""
        # TODO: Implement generic OIDC token verification
        return None

    def refresh_token(self, user: AuthUser) -> str:
        """Generate a new access token for an existing user."""
        return self.create_token(user)
