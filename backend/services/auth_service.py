from fastapi import HTTPException, Request
from typing import Optional, Tuple
import logging
from db.supabase_client import get_client

class AuthService:
    @staticmethod
    async def validate_user(request: Request) -> str:
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
            token = auth_header.split(" ")[1]
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                raise HTTPException(status_code=401, detail="Invalid user token")
                
            return user.user.id
        except Exception as e:
            logging.error(f"User validation error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    @staticmethod
    async def get_tokens_from_request(request: Request) -> Tuple[str, str]:
        auth_header = request.headers.get("Authorization")
        refresh_token = request.headers.get("X-Refresh-Token")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        access_token = auth_header.split(" ")[1]
        return access_token, refresh_token

    @staticmethod
    async def get_user(token: str):
        try:
            supabase = get_client()
            user = supabase.auth.get_user(token)
            return user
        except Exception as e:
            logging.error(f"Failed to get user: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")