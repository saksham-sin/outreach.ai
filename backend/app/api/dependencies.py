"""API dependencies - authentication, database sessions, etc."""

from typing import Annotated
import secrets
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# OAuth2 scheme for JWT bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# HTTP Basic auth for webhooks
http_basic = HTTPBasic(auto_error=False)

# Database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    token: str | None = Depends(oauth2_scheme),
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        session: Database session
        token: JWT access token from Authorization header
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(session)
    user_id = auth_service.verify_access_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    session: SessionDep,
    token: str | None = Depends(oauth2_scheme),
) -> User | None:
    """
    Optional user dependency - returns None if not authenticated.
    
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if not token:
        return None
    
    try:
        return await get_current_user(session, token)
    except HTTPException:
        return None


def verify_webhook_auth(
    credentials: HTTPBasicCredentials | None = Depends(http_basic),
) -> bool:
    """
    Verify HTTP Basic authentication for webhook endpoints.
    
    Args:
        credentials: Basic auth credentials
        
    Returns:
        True if authenticated
        
    Raises:
        HTTPException: If credentials invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Use constant-time comparison to prevent timing attacks
    username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"),
        settings.WEBHOOK_USERNAME.encode("utf8"),
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        settings.WEBHOOK_PASSWORD.encode("utf8"),
    )
    
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return True


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
WebhookAuth = Annotated[bool, Depends(verify_webhook_auth)]
