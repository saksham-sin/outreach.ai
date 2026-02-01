"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.dependencies import SessionDep, CurrentUser
from app.services.auth_service import AuthService, AuthenticationError
from app.models.user import UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


class MagicLinkRequest(BaseModel):
    """Request to send a magic link."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response after sending a magic link."""
    message: str


class VerifyTokenRequest(BaseModel):
    """Request to verify a magic link token."""
    token: str


class TokenResponse(BaseModel):
    """Response containing access token."""
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/magic-link",
    response_model=MagicLinkResponse,
    summary="Request magic link",
    description="Send a magic link to the provided email address for passwordless authentication.",
)
async def request_magic_link(
    request: MagicLinkRequest,
    session: SessionDep,
) -> MagicLinkResponse:
    """
    Request a magic link for authentication.
    
    A magic link will be sent to the provided email address.
    The link expires after a configured time (default: 15 minutes).
    """
    auth_service = AuthService(session)
    
    try:
        await auth_service.send_magic_link(request.email)
        return MagicLinkResponse(message="Magic link sent to your email")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/verify",
    response_model=TokenResponse,
    summary="Verify magic link",
    description="Verify a magic link token and receive an access token.",
)
async def verify_magic_link(
    request: VerifyTokenRequest,
    session: SessionDep,
) -> TokenResponse:
    """
    Verify a magic link token and get an access token.
    
    The magic link token is included in the URL sent to the user's email.
    Returns a JWT access token for authenticated API requests.
    """
    auth_service = AuthService(session)
    
    try:
        user, access_token = await auth_service.verify_and_login(request.token)
        return TokenResponse(access_token=access_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserRead:
    """
    Get the current authenticated user's information.
    
    Requires a valid access token in the Authorization header.
    """
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )
