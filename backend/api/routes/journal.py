from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from services.journal_service import JournalService
from services.database_service import DatabaseService
from services.auth_service import AuthService

router = APIRouter(prefix="/journal", tags=["journal"])

class JournalEntryRequest(BaseModel):
    content: str

@router.post("/analyze")
async def analyze_entry(entry: JournalEntryRequest):
    return await JournalService.analyze_entry(entry.content)

@router.post("/entry")
async def create_journal_entry(entry: JournalEntryRequest, request: Request):
    user_id = await AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    
    entry_result = await DatabaseService.create_journal_entry(user_id, entry.content)
    if not entry_result.data:
        raise HTTPException(status_code=500, detail="Failed to save journal entry")
        
    entry_id = entry_result.data[0]['id']
    analysis = await JournalService.analyze_entry(entry.content)
    await DatabaseService.save_analysis(entry_id, analysis["analysis"])
    
    return {"status": "success", "data": {"entry": entry_result.data[0], "analysis": analysis["analysis"]}}

@router.get("/entries")
async def get_entries(
    request: Request, 
    search: str = None, 
    start_date: str = None, 
    end_date: str = None
):
    user_id = await AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    
    return await JournalService.get_entries(
        user_id, 
        search_term=search, 
        start_date=start_date, 
        end_date=end_date
    )


