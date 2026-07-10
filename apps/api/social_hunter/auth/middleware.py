"""Authentication middleware for Social Hunter."""
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


class AuthContext:
    """Authenticated user context."""

    def __init__(
        self,
        user_id: str,
        email: str | None = None,
        plan: str = "free",
        monthly_searches_used: int = 0,
        monthly_search_limit: int = 10,
    ):
        self.user_id = user_id
        self.email = email
        self.plan = plan
        self.monthly_searches_used = monthly_searches_used
        self.monthly_search_limit = monthly_search_limit

    @property
    def can_search(self) -> bool:
        """Check if user can perform a search."""
        if self.plan == "unlimited":
            return True
        return self.monthly_searches_used < self.monthly_search_limit

    def increment_search(self) -> None:
        """Increment search counter."""
        self.monthly_searches_used += 1


class ClerkAuthProvider:
    """Clerk authentication provider."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.api_url = "https://api.clerk.dev/v1"

    async def verify_token(self, token: str) -> AuthContext:
        """Verify JWT token and return user context."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )

            user_data = response.json()

            # Get user metadata for plan info
            metadata = user_data.get("private_metadata", {})

            return AuthContext(
                user_id=user_data["id"],
                email=user_data.get("email_addresses", [{}])[0].get("email_address"),
                plan=metadata.get("plan", "free"),
                monthly_searches_used=metadata.get("monthly_searches_used", 0),
                monthly_search_limit=metadata.get("monthly_search_limit", 10),
            )


class Auth0AuthProvider:
    """Auth0 authentication provider."""

    def __init__(self, domain: str, audience: str):
        self.domain = domain
        self.audience = audience
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"

    async def verify_token(self, token: str) -> AuthContext:
        """Verify Auth0 JWT token."""
        import jwt
        from jwt import PyJWKClient

        try:
            jwks_client = PyJWKClient(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/",
            )

            # Get app metadata for plan info
            app_metadata = payload.get("app_metadata", {})

            return AuthContext(
                user_id=payload["sub"],
                email=payload.get("email"),
                plan=app_metadata.get("plan", "free"),
                monthly_searches_used=app_metadata.get("monthly_searches_used", 0),
                monthly_search_limit=app_metadata.get("monthly_search_limit", 10),
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            )


# Configuration - load from environment
import os

AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "demo")  # "clerk", "auth0", or "demo"
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")

# Initialize provider
if AUTH_PROVIDER == "clerk" and CLERK_SECRET_KEY:
    auth_provider = ClerkAuthProvider(CLERK_SECRET_KEY)
elif AUTH_PROVIDER == "auth0" and AUTH0_DOMAIN:
    auth_provider = Auth0AuthProvider(AUTH0_DOMAIN, AUTH0_AUDIENCE)
else:
    auth_provider = None  # Demo mode


async def get_auth_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthContext:
    """Dependency to get authenticated user context."""

    if auth_provider is None:
        # Demo mode - return test user
        return AuthContext(
            user_id="demo-analyst",
            email="demo@example.com",
            plan="unlimited",
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await auth_provider.verify_token(credentials.credentials)


async def require_auth(
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> AuthContext:
    """Require authentication."""
    return context


async def require_paid_plan(
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> AuthContext:
    """Require paid plan."""
    if context.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires a paid plan",
        )
    return context
