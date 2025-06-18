"""Authentication dependencies for FastAPI."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from gotrue.types import User
from app.auth.supabase import supabase_auth

# Security scheme for JWT Bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Extracts the JWT token from the Authorization header and validates it
    with Supabase.
    """
    token = credentials.credentials
    
    # Verify token with Supabase
    user = await supabase_auth.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional authentication dependency.
    
    Returns the user if authenticated, None otherwise.
    Useful for endpoints that have different behavior for authenticated users.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return await supabase_auth.verify_token(token)
