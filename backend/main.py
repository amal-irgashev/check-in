from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from auth.auth import auth_middleware
from services.database_service import DatabaseService
from services.auth_service import AuthService
from services.profile_service import ProfileService
from services.journal_service import JournalService
from ai_agents.chatbot import get_chat_response
from db.supabase_client import get_client
from fastapi.responses import StreamingResponse
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware setup
public_paths = {"/", "/docs", "/openapi.json"}

@app.middleware("http")
async def auth_middleware_with_public_paths(request: Request, call_next):
    if request.url.path in public_paths:
        return await call_next(request)
    return await auth_middleware(request, call_next)

# Request models
class JournalEntryRequest(BaseModel):
    content: str

class ChatRequest(BaseModel):
    message: str

# Routes
@app.post("/analyze-entry")
async def analyze_entry(entry: JournalEntryRequest):
    return await JournalService.analyze_entry(entry.content)

@app.post("/journal-entry")
async def create_journal_entry(entry: JournalEntryRequest, request: Request):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    
    entry_result = await DatabaseService.create_journal_entry(user_id, entry.content)
    if not entry_result.data:
        raise HTTPException(status_code=500, detail="Failed to save journal entry")
        
    entry_id = entry_result.data[0]['id']
    analysis = await JournalService.analyze_entry(entry.content)
    await DatabaseService.save_analysis(entry_id, analysis["analysis"])
    
    return {"status": "success", "data": {"entry": entry_result.data[0], "analysis": analysis["analysis"]}}

@app.get("/entries")
async def get_entries(
    request: Request,
    search: str = None,
    start_date: str = None,
    end_date: str = None
):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    return await JournalService.get_entries(
        user_id, 
        search_term=search, 
        start_date=start_date, 
        end_date=end_date
    )

@app.post("/chat")
async def chat(request: ChatRequest, req: Request):
    try:
        user_id = AuthService.validate_user(req)
        access_token, refresh_token = AuthService.get_tokens_from_request(req)
        DatabaseService.set_auth_session(access_token, refresh_token)
        
        async def generate():
            try:
                async for token in get_chat_response(user_id, request.message):
                    yield f"data: {json.dumps({'token': token})}\n\n"
            except Exception as e:
                logging.error(f"Chat error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/stats")
async def get_profile_stats(request: Request):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    return await ProfileService.get_stats(user_id)

@app.post("/api/profile/update")
async def update_profile(request: Request, data: dict):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    supabase = get_client()
    return await ProfileService.update_profile(supabase, data)

@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, request: Request):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    return await JournalService.delete_entry(user_id, entry_id)

@app.get("/")
def read_root():
    return {"message": "API is running!"}