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
    async def get_entries(user_id: str, search_term: str = None, start_date: str = None, end_date: str = None):
        try:
            supabase = get_client()
            query = supabase.table("journal_entries")\
                .select("*, journal_analyses(*)")\
                .eq('user_id', user_id)
            
            # Add search filter if search term is provided
            if search_term:
                query = query.ilike('entry', f'%{search_term}%')
            
            # Add date range filters if provided
            if start_date:
                query = query.gte('created_at', start_date)
            if end_date:
                query = query.lte('created_at', end_date)
            
            # Order by date
            query = query.order('created_at', desc=True)
            
            # Execute query and log results
            result = query.execute()
            logging.info(f"Fetched entries count: {len(result.data) if result.data else 0}")
            logging.info(f"Query result: {result.data}")
            
            return result.data or []
        except Exception as e:
            logging.error(f"Failed to fetch entries: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# delete entry
    @staticmethod
    async def delete_entry(user_id: str, entry_id: str):
        try:
            supabase = get_client()
            
            # First verify the entry belongs to the user
            entry = supabase.table("journal_entries")\
                .select("id")\
                .eq('id', entry_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
                
            if not entry.data:
                raise HTTPException(status_code=404, detail="Entry not found")
                
            # Delete associated analyses first (due to foreign key constraint)
            supabase.table("journal_analyses")\
                .delete()\
                .eq('entry_id', entry_id)\
                .execute()
                
            # Delete the entry
            result = supabase.table("journal_entries")\
                .delete()\
                .eq('id', entry_id)\
                .execute()
                
            return {"status": "success", "message": "Entry deleted successfully"}
        except Exception as e:
            logging.error(f"Failed to delete entry: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))