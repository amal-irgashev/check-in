from fastapi import HTTPException
from db.supabase_client import get_client
import logging

class ProfileService:
    @staticmethod
    async def get_stats(user_id: str):
        supabase = get_client()
        
        try:
            # Get user from current session
            user = supabase.auth.get_user()
            if not user:
                raise HTTPException(status_code=401, detail="User not authenticated")
                
            name = user.user.user_metadata.get('full_name')
                
            # Get total entries count
            entries_result = supabase.table("journal_entries")\
                .select("created_at", count="exact")\
                .eq('user_id', user_id)\
                .execute()
                
            total_entries = entries_result.count if hasattr(entries_result, 'count') else len(entries_result.data or [])
            
            # Get first entry date
            first_entry_result = supabase.table("journal_entries")\
                .select("created_at")\
                .eq('user_id', user_id)\
                .order('created_at')\
                .limit(1)\
                .execute()
                
            member_since = first_entry_result.data[0]['created_at'] if first_entry_result.data else None
            
            return {
                "full_name": name,
                "total_entries": total_entries,
                "member_since": member_since
            }
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Failed to fetch profile stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve profile statistics"
            )

    @staticmethod
    async def update_profile(supabase_client, data: dict):
        try:
            # Only update auth metadata
            auth_update = supabase_client.auth.update_user({
                "data": {"full_name": data.get("full_name")}
            })
            
            if not auth_update:
                raise HTTPException(status_code=500, detail="Failed to update user profile")
            
            return auth_update.user
        except Exception as e:
            logging.error(f"Error updating user profile: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))