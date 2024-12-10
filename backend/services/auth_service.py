# auth service

from fastapi import HTTPException, Request
from typing import Optional, Tuple
import logging
from db.supabase_client import get_client
 
class AuthService:
    @staticmethod
    async def validate_user(request: Request) -> str:
        """Validate user from request and return user_id"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        try:
            token = auth_header.split(" ")[1]
            user = get_client().auth.get_user(token).user
            if not user:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            return user.id
            
        except Exception as e:
            logging.error(f"User validation failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    # get tokens from request
    @staticmethod
    async def get_tokens_from_request(request: Request) -> Tuple[str, Optional[str]]:
        """Get access and refresh tokens from request headers"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        try:
            return auth_header.split(" ")[1], request.headers.get("X-Refresh-Token")
        except Exception as e:
            logging.error(f"Failed to get tokens from request: {str(e)}")
            raise HTTPException(status_code=401, detail="Failed to extract authentication tokens")
        
        
    # get user from token
    @staticmethod
    async def get_user(token: str):
        """Get user from token"""
        try:
            return get_client().auth.get_user(token)
        except Exception as e:
            logging.error(f"Failed to get user: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")