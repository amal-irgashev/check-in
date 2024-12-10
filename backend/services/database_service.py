from typing import List, Optional
from fastapi import HTTPException
from db.supabase_client import get_client
import logging
from dataclasses import dataclass
from typing import Dict

@dataclass
class DatabaseResult:
    data: Optional[List[Dict]]
    error: Optional[str] = None

class DatabaseService:
    @staticmethod
    async def set_auth_session(access_token: str, refresh_token: Optional[str] = None) -> None:
        try:
            supabase = get_client()
            if not access_token:
                raise ValueError("Access token is required")
            supabase.auth.set_session(access_token, refresh_token)
        except Exception as e:
            logging.error(f"Error setting auth session: {str(e)}")
            raise HTTPException(
                status_code=401, 
                detail="Failed to set authentication session"
            )

    @staticmethod
    async def create_journal_entry(user_id: str, content: str):
        supabase = get_client()
        entry_data = {
            "entry": content,
            "user_id": user_id,
            "created_at": "now()"
        }
        return supabase.table("journal_entries").insert(entry_data).execute()
        
    @staticmethod
    async def save_analysis(entry_id: str, analysis: dict):
        supabase = get_client()
        analysis_data = {
            "entry_id": entry_id,
            "mood": analysis["mood"],
            "summary": analysis["summary"],
            "categories": analysis["categories"],
            "key_insights": analysis["key_insights"],
            "created_at": "now()"
        }
        return supabase.table("journal_analyses").insert(analysis_data).execute()
        
    @staticmethod
    async def get_user_entries(user_id: str):
        supabase = get_client()
        return supabase.table("journal_entries")\
            .select("*, journal_analyses(*)")\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
    @staticmethod
    def get_recent_entries(user_id: str, limit: int = 3) -> DatabaseResult:
        """
        Fetches recent journal entries with their analyses for a user.
        """
        try:
            supabase = get_client()
            result = supabase.table("journal_entries")\
                .select("*, journal_analyses(*)")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
                
            return DatabaseResult(data=result.data)
        except Exception as e:
            logging.error(f"Failed to fetch recent entries: {str(e)}")
            return DatabaseResult(data=None, error=str(e))