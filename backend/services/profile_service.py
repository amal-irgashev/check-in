from fastapi import HTTPException
from db.supabase_client import get_client
import logging

class ProfileService:
    @staticmethod
    async def get_stats(user_id: str):
        supabase = get_client()
        
        try:
            entries = supabase.table("journal_entries")\
                .select("created_at", count="exact")\
                .eq('user_id', user_id)\
                .execute()
                
            total_entries = entries.count if entries.count is not None else 0
            
            first_entry = supabase.table("journal_entries")\
                .select("created_at")\
                .eq('user_id', user_id)\
                .order('created_at')\
                .limit(1)\
                .execute()
                
            member_since = first_entry.data[0]['created_at'] if first_entry.data else None
            
            return {
                "total_entries": total_entries,
                "member_since": member_since
            }
        except Exception as e:
            logging.error(f"Failed to fetch profile stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_profile(supabase_client, data: dict):
        try:
            # Update auth metadata
            auth_update = supabase_client.auth.update_user({
                "data": {"full_name": data.get("full_name")}
            })
            
            if not auth_update:
                raise HTTPException(status_code=500, detail="Failed to update user profile")
            
            # Update users table
            users_update = supabase_client.table('users')\
                .update({"name": data.get("full_name")})\
                .eq('id', auth_update.user.id)\
                .execute()
                
            if not users_update:
                raise HTTPException(status_code=500, detail="Failed to update user table")
                
            return auth_update.user
        except Exception as e:
            logging.error(f"Error updating user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))