import os
from supabase import create_client
from fastapi import Request, HTTPException
import logging
from db.supabase_client import get_client

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class AuthService:
    @staticmethod
    async def sign_up(email: str, password: str):
        try:
            return supabase.auth.sign_up({
                "email": email,
                "password": password
            })
        except Exception as e:
            raise Exception(f"Error during sign up: {str(e)}")

    @staticmethod
    async def sign_in(email: str, password: str):
        try:
            return supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as e:
            raise Exception(f"Error during sign in: {str(e)}")

    @staticmethod
    async def sign_out():
        try:
            return supabase.auth.sign_out()
        except Exception as e:
            raise Exception(f"Error during sign out: {str(e)}")

    @staticmethod
    async def get_user(access_token: str):
        try:
            response = supabase.auth.get_user(access_token)
            if not response or not response.user:
                raise Exception("No user found")
            return response
        except Exception as e:
            logging.error(f"Error in get_user: {str(e)}")
            raise Exception(f"Error getting user: {str(e)}")

async def auth_middleware(request: Request, call_next):
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    token = auth_header.split(' ')[1]
    refresh_token = request.headers.get('X-Refresh-Token')
    
    try:
        user_response = await AuthService.get_user(token)
        request.state.user = user_response.user
        request.state.access_token = token
        request.state.refresh_token = refresh_token
        return await call_next(request)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")