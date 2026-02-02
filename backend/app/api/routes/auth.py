"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.dependencies import SessionDep, CurrentUser
from app.services.auth_service import AuthService, AuthenticationError
from app.models.user import UserRead, UserProfileUpdate
from app.infrastructure.llm import get_llm_client

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
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        company_name=current_user.company_name,
        job_title=current_user.job_title,
        email_signature=current_user.email_signature,
        profile_completed=current_user.profile_completed,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update user profile",
    description="Update the current user's profile information.",
)
async def update_profile(
    data: UserProfileUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserRead:
    """Update current user's profile."""
    auth_service = AuthService(session)
    user = await auth_service.update_user_profile(current_user.id, data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        company_name=user.company_name,
        job_title=user.job_title,
        email_signature=user.email_signature,
        profile_completed=user.profile_completed,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/generate-signature",
    response_model=dict,
    summary="Generate email signature with AI",
    description="Generate a professional email signature using AI based on user profile.",
)
async def generate_signature(
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    """Generate an email signature using AI based on user profile."""
    # Fetch fresh user data
    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate required fields
    if not all([user.first_name, user.last_name, user.job_title, user.company_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile (name, title, company) before generating a signature",
        )
    
    full_name = f"{user.first_name} {user.last_name}"
    
    llm = get_llm_client()
    
    try:
        signature_html = await llm.generate_signature(
            full_name=full_name,
            job_title=user.job_title,
            company_name=user.company_name,
            email=user.email,
        )
        return {"signature_html": signature_html}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signature",
        )
