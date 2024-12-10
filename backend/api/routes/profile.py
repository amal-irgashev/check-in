from fastapi import APIRouter, Request, HTTPException, Depends
from services.profile_service import ProfileService
from db.supabase_client import get_client
from ..dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/stats")
async def get_profile_stats(user_id: str = Depends(get_current_user)):
    return await ProfileService.get_stats(user_id)

@router.post("/update")
async def update_profile(
    data: dict,
    user_id: str = Depends(get_current_user)
):
    return await ProfileService.update_profile(get_client(), data)
