"""Authentication service - magic link flow and JWT management."""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.prompts import MAGIC_LINK_EMAIL_SUBJECT, MAGIC_LINK_EMAIL_BODY
from app.core.constants import MAGIC_LINK_PATH
from app.models.user import User, UserCreate, UserRead
from app.infrastructure.email_factory import get_email_provider
from app.infrastructure.email_provider import EmailProviderError

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.email_provider = get_email_provider()

    async def get_or_create_user(self, email: str) -> User:
        """Get existing user or create new one."""
        # Check if user exists
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Create new user
        user = User(email=email.lower())
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info(f"Created new user: {email}")
        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    def create_magic_link_token(self, email: str) -> str:
        """
        Create a JWT token for magic link authentication.
        
        Args:
            email: User's email address
            
        Returns:
            JWT token string
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )
        payload = {
            "sub": email.lower(),
            "exp": expire,
            "type": "magic_link",
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_magic_link_token(self, token: str) -> Optional[str]:
        """
        Verify a magic link token and return the email.
        
        Args:
            token: JWT token from magic link
            
        Returns:
            Email address if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            
            if payload.get("type") != "magic_link":
                logger.warning("Invalid token type for magic link")
                return None
            
            return payload.get("sub")
            
        except jwt.ExpiredSignatureError:
            logger.warning("Magic link token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid magic link token: {str(e)}")
            return None

    def create_access_token(self, user_id: UUID) -> str:
        """
        Create an access token for authenticated sessions.
        
        Args:
            user_id: User's UUID
            
        Returns:
            JWT access token string
        """
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.ACCESS_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_access_token(self, token: str) -> Optional[UUID]:
        """
        Verify an access token and return the user ID.
        
        Args:
            token: JWT access token
            
        Returns:
            User UUID if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            
            if payload.get("type") != "access":
                return None
            
            user_id_str = payload.get("sub")
            if not user_id_str:
                return None
            
            return UUID(user_id_str)
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except ValueError:
            return None

    async def send_magic_link(self, email: str) -> bool:
        """
        Generate and send a magic link email.
        
        Args:
            email: User's email address
            
        Returns:
            True if email sent successfully
            
        Raises:
            AuthenticationError: If email fails to send
        """
        # Create the token
        token = self.create_magic_link_token(email)
        
        # Build the magic link URL
        magic_link = f"{settings.FRONTEND_URL}{MAGIC_LINK_PATH}?token={token}"
        
        # Format email body
        body = MAGIC_LINK_EMAIL_BODY.format(
            magic_link=magic_link,
            expire_minutes=settings.MAGIC_LINK_EXPIRE_MINUTES,
        )
        
        result = await self.email_provider.send_transactional_email(
            to_email=email,
            subject=MAGIC_LINK_EMAIL_SUBJECT,
            body=body,
        )
        
        if not result.success:
            logger.error(f"Failed to send magic link to {email}: {result.error}")
            raise AuthenticationError(f"Failed to send magic link: {result.error}")
        
        logger.info(f"Magic link sent to {email}")
        return True

    async def verify_and_login(self, token: str) -> tuple[User, str]:
        """
        Verify magic link token and return user with access token.
        
        Args:
            token: Magic link JWT token
            
        Returns:
            Tuple of (User, access_token)
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        email = self.verify_magic_link_token(token)
        if not email:
            raise AuthenticationError("Invalid or expired magic link")
        
        # Get or create user
        user = await self.get_or_create_user(email)
        
        # Create access token
        access_token = self.create_access_token(user.id)
        
        logger.info(f"User logged in: {email}")
        return user, access_token
