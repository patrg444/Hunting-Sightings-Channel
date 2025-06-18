"""Supabase authentication integration."""

from typing import Optional
from supabase import create_client, Client
from gotrue.types import Session, User
from app.config import get_settings

settings = get_settings()


class SupabaseAuth:
    """Handle Supabase authentication operations."""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user if valid."""
        try:
            # Get user from token
            response = self.client.auth.get_user(token)
            return response.user if response else None
        except Exception:
            return None
    
    async def sign_up(self, email: str, password: str) -> dict:
        """Sign up a new user."""
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sign_in(self, email: str, password: str) -> dict:
        """Sign in an existing user."""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sign_out(self, token: str) -> bool:
        """Sign out a user."""
        try:
            self.client.auth.sign_out(token)
            return True
        except Exception:
            return False
    
    async def reset_password_request(self, email: str, redirect_url: str) -> dict:
        """Request password reset."""
        try:
            self.client.auth.reset_password_for_email(
                email,
                {"redirect_to": redirect_url}
            )
            return {
                "success": True,
                "message": "Password reset email sent"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_password(self, token: str, new_password: str) -> dict:
        """Update user password."""
        try:
            response = self.client.auth.update_user(
                {"password": new_password},
                token
            )
            return {
                "success": True,
                "user": response.user
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
supabase_auth = SupabaseAuth()
