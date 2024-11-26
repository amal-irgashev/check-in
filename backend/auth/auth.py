# Add auth with supabase {https://supabase.com/docs/guides/auth}

# maybe just with google for now

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import uuid
from typing import Optional
from db.models import User
from fastapi import Request, HTTPException
import logging
from db.supabase_client import get_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class AuthService:
    @staticmethod
    def _get_client() -> Client:
        return get_client()

    @staticmethod
    async def sign_up(email: str, password: str):
        try:
            # 1. Create auth user in Supabase
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # 2. Create user record in our database
            user_data = {
                "id": auth_response.user.id,  # Use Supabase auth user ID
                "email": email,
                "email_verified": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Insert into our 'users' table
            db_response = supabase.table('users').insert(user_data).execute()
            
            return auth_response
        except Exception as e:
            raise Exception(f"Error during sign up: {str(e)}")

    @staticmethod
    async def sign_in(email: str, password: str):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            raise Exception(f"Error during sign in: {str(e)}")

    @staticmethod
    async def sign_out():
        try:
            response = supabase.auth.sign_out()
            return response
        except Exception as e:
            raise Exception(f"Error during sign out: {str(e)}")

    @staticmethod
    async def get_user(access_token: str):
        try:
            logging.info("Calling Supabase get_user...")
            response = supabase.auth.get_user(access_token)
            logging.info(f"Supabase get_user response: {response}")
            if not response or not response.user:
                logging.error("No user found in Supabase response")
                raise Exception("No user found")
            return response
        except Exception as e:
            logging.error(f"Error in get_user: {str(e)}")
            raise Exception(f"Error getting user: {str(e)}")

    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[User]:
        try:
            response = supabase.table('users').select("*").eq('id', user_id).single().execute()
            if response.data:
                return User(**response.data)
            return None
        except Exception as e:
            raise Exception(f"Error fetching user profile: {str(e)}")

async def auth_middleware(request: Request, call_next):
    logging.info("=== Auth Middleware Start ===")
    auth_header = request.headers.get('Authorization')
    logging.info(f"Headers received: {dict(request.headers)}")
    
    if not auth_header or not auth_header.startswith('Bearer '):
        logging.error("No Bearer token found in Authorization header")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    token = auth_header.split(' ')[1]
    refresh_token = request.headers.get('X-Refresh-Token')  # Get refresh token from header
    logging.info(f"Token extracted: {token[:10]}...")
    
    try:
        logging.info("Attempting to validate token with Supabase...")
        user_response = await AuthService.get_user(token)
        logging.info(f"User response received: {user_response}")
        request.state.user = user_response.user
        request.state.access_token = token
        request.state.refresh_token = refresh_token
        response = await call_next(request)
        logging.info("=== Auth Middleware End ===")
        return response
    except Exception as e:
        logging.error(f"Detailed auth error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

