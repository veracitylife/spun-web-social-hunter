"""Authentication middleware for FastAPI."""
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from social_hunter.services.auth import AuthService, AuthUser


class AuthMiddleware:
    """HTTP middleware for JWT token extraction and validation."""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.scheme = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request) -> Optional[AuthUser]:
        """Extract and verify JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Demo/fallback: return demo user
            return AuthUser(
                user_id="demo-user",
                email="demo@social-hunter.local",
                name="Demo User",
                plan_id="professional",
                roles=["analyst"],
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization scheme",
                )
            user = self.auth_service.verify_token(token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
            return user
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
            )


def get_current_user(request: Request) -> Optional[AuthUser]:
    """Dependency for FastAPI endpoints to get authenticated user."""
    return getattr(request.state, "user", None)
