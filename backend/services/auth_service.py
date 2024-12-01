from fastapi import HTTPException, Request
from typing import Optional
import logging
from db.supabase_client import get_client

class AuthService:
    @staticmethod
    def get_tokens_from_request(request: Request) -> tuple[str, Optional[str]]:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        access_token = auth_header.split(' ')[1]
        refresh_token = request.headers.get('X-Refresh-Token')
        return access_token, refresh_token
        
    @staticmethod
    def validate_user(request: Request):
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        return request.state.user.id