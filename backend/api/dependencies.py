from fastapi import Request
from services.auth_service import AuthService
from services.database_service import DatabaseService

async def get_current_user(request: Request):
    """Common dependency for authenticated endpoints"""
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    return user_id
