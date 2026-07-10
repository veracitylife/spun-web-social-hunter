"""Authentication endpoints for token generation and user info."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from social_hunter.middleware.auth import get_current_user
from social_hunter.services.auth import AuthService, AuthUser, AuthConfig

router = APIRouter(prefix="/api/auth", tags=["auth"])


class TokenRequest(BaseModel):
    """Request to generate a token (placeholder for provider token exchange)."""
    provider_token: str  # Token from Auth0, Okta, or OIDC provider
    provider: str = "oidc"  # "auth0", "okta", "oidc", "mock"


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: AuthUser


class UserInfoResponse(BaseModel):
    """Current user info response."""
    user: AuthUser


# Initialize auth service (production: inject from FastAPI dependency)
auth_config = AuthConfig()
auth_service = AuthService(auth_config)


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest) -> TokenResponse:
    """
    Exchange provider token for application JWT.
    TODO: Implement provider token verification.
    """
    user = await auth_service.authenticate_with_provider(request.provider_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid provider token",
        )
    token = auth_service.create_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=auth_config.token_expiry_minutes * 60,
        user=user,
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(user: AuthUser = None) -> UserInfoResponse:
    """
    Get current authenticated user info.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return UserInfoResponse(user=user)


@router.post("/refresh")
async def refresh_token(user: AuthUser = None) -> TokenResponse:
    """
    Refresh an access token.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    new_token = auth_service.refresh_token(user)
    return TokenResponse(
        access_token=new_token,
        expires_in=auth_config.token_expiry_minutes * 60,
        user=user,
    )


@router.post("/logout")
async def logout(user: AuthUser = None) -> dict:
    """
    Logout endpoint (client-side token revocation).
    TODO: Implement token blacklisting if using Redis.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {"status": "logged_out", "user_id": user.user_id}
