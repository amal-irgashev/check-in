from fastapi import HTTPException
from db.supabase_client import get_client
from ai_agents.ai_analysis import analyze_journal_entry
import logging

class JournalService:
    @staticmethod
    async def analyze_entry(content: str):
        try:
            analysis = analyze_journal_entry(content)
            return {"status": "success", "analysis": analysis}
        except Exception as e:
            logging.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_entries(user_id: str):
        try:
            supabase = get_client()
            entries = supabase.table("journal_entries")\
                .select("*, journal_analyses(*)")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
                
            return entries.data or []
        except Exception as e:
            logging.error(f"Failed to fetch entries: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))