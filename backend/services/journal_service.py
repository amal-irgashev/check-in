from fastapi import HTTPException
from db.supabase_client import get_client
from ai_agents.ai_analysis import analyze_journal_entry
import logging
from typing import Optional, Dict, List, Any

class JournalService:
    """Service class for handling journal-related operations"""
    
    @staticmethod
    async def analyze_entry(content: str) -> Dict[str, Any]:
        """Analyze a journal entry's content"""
        try:
            analysis = analyze_journal_entry(content)
            return {"status": "success", "analysis": analysis}
        except Exception as e:
            logging.error(f"Analysis failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze journal entry"
            )

    # get journal entries!
    @staticmethod
    async def get_entries(
        user_id: str,
        search_term: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve journal entries with optional filtering"""
        try:
            supabase = get_client()
            
            # Build base query
            query = supabase.table("journal_entries")\
                .select("*, journal_analyses(*)")\
                .eq('user_id', user_id)
            
            # Add filters
            if search_term:
                query = query.ilike('entry', f'%{search_term}%')
            
            # Handle date filtering
            if start_date:
                query = query.gte('created_at', f"{start_date}T00:00:00")
            if end_date:
                # Add one day to include entries on the end date
                query = query.lt('created_at', f"{end_date}T23:59:59")
            
            # Add ordering
            query = query.order('created_at', desc=True)
            
            # Execute query
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logging.error(f"Failed to fetch entries: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve journal entries: {str(e)}"
            )
            

# delete the entry

    @staticmethod
    async def delete_entry(user_id: str, entry_id: str) -> Dict[str, str]:
        """Delete a journal entry and its associated analyses"""
        try:
            supabase = get_client()
            
            # Verify entry ownership
            entry = supabase.table("journal_entries")\
                .select("id")\
                .eq('id', entry_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
                
            if not entry.data:
                raise HTTPException(
                    status_code=404,
                    detail="Entry not found or access denied"
                )
                
            # Delete associated analyses first
            supabase.table("journal_analyses")\
                .delete()\
                .eq('entry_id', entry_id)\
                .execute()
                
            # Delete the entry
            supabase.table("journal_entries")\
                .delete()\
                .eq('id', entry_id)\
                .execute()
                
            return {
                "status": "success",
                "message": "Entry deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Failed to delete entry: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete journal entry"
            )