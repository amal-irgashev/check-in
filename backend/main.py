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
async def get_entries(request: Request):
    user_id = AuthService.validate_user(request)
    access_token, refresh_token = AuthService.get_tokens_from_request(request)
    DatabaseService.set_auth_session(access_token, refresh_token)
    return await JournalService.get_entries(user_id)

@app.post("/chat")
async def chat(request: ChatRequest, request_obj: Request):
    user_id = request_obj.state.user.id
    response = get_chat_response(user_id, request.message)
    return {"response": response}

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

@app.get("/")
def read_root():
    return {"message": "API is running!"}