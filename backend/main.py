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
from services.chat_service import ChatService
from datetime import datetime

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
@app.middleware("http")
async def auth_middleware_handler(request: Request, call_next):
    public_paths = {"/", "/docs", "/openapi.json"}
    if request.url.path in public_paths:
        return await call_next(request)
    return await auth_middleware(request, call_next)

# Request db models
class JournalEntryRequest(BaseModel):
    content: str

class ChatRequest(BaseModel):
    message: str
    window_id: str

# Helper function for common auth setup
async def setup_auth_session(request: Request):
    user_id = await AuthService.validate_user(request)
    access_token, refresh_token = await AuthService.get_tokens_from_request(request)
    supabase = get_client()
    await DatabaseService.set_auth_session(access_token, refresh_token)
    return user_id

# Routes
@app.post("/analyze-entry")
async def analyze_entry(entry: JournalEntryRequest):
    return await JournalService.analyze_entry(entry.content)

@app.post("/journal-entry")
async def create_journal_entry(entry: JournalEntryRequest, request: Request):
    user_id = await setup_auth_session(request)
    
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
    try:
        user_id = await setup_auth_session(request)
        
        # Validate dates if provided
        formatted_start_date = None
        formatted_end_date = None
        
        if start_date:
            try:
                parsed_date = datetime.fromisoformat(start_date)
                formatted_start_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid start_date format. Expected YYYY-MM-DD"
                )
                
        if end_date:
            try:
                parsed_date = datetime.fromisoformat(end_date)
                formatted_end_date = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid end_date format. Expected YYYY-MM-DD"
                )
        
        # Ensure end_date is not before start_date
        if formatted_start_date and formatted_end_date:
            if formatted_end_date < formatted_start_date:
                raise HTTPException(
                    status_code=400,
                    detail="end_date cannot be before start_date"
                )
        
        entries = await JournalService.get_entries(
            user_id, 
            search_term=search, 
            start_date=formatted_start_date, 
            end_date=formatted_end_date
        )
        
        return entries
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_entries: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    try:
        user_id = await setup_auth_session(request)
        window_id = chat_request.window_id
        
        async def generate():
            async for token in get_chat_response(user_id, chat_request.message, window_id):
                yield f"data: {json.dumps({'token': token})}\n\n"
                
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/stats")
async def get_profile_stats(request: Request):
    try:
        user_id = await setup_auth_session(request)
        return await ProfileService.get_stats(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_profile_stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile stats")

@app.post("/api/profile/update")
async def update_profile(request: Request, data: dict):
    await setup_auth_session(request)
    return await ProfileService.update_profile(get_client(), data)

@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, request: Request):
    user_id = await setup_auth_session(request)
    return await JournalService.delete_entry(user_id, entry_id)

@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.post("/chat/window/create")
async def create_chat_window(request: Request):
    try:
        user_id = await setup_auth_session(request)
        window = await ChatService.create_chat_window(user_id)
        return window
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/windows")
async def get_chat_windows(request: Request):
    try:
        user_id = await setup_auth_session(request)
        windows = await ChatService.get_chat_windows(user_id)
        return windows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{window_id}")
async def get_window_history(window_id: str, request: Request):
    try:
        user_id = await setup_auth_session(request)
        history = await ChatService.get_chat_history(user_id, window_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/window/{window_id}")
async def delete_chat_window(window_id: str, request: Request):
    try:
        user_id = await setup_auth_session(request)
        success = await ChatService.delete_window(user_id, window_id)
        if success:
            return {"message": "Chat window deleted successfully"}
        raise HTTPException(status_code=404, detail="Chat window not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/chat/window/{window_id}/rename")
async def rename_chat_window(window_id: str, request: Request, data: dict):
    try:
        user_id = await setup_auth_session(request)
        new_title = data.get("title")
        if not new_title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        success = await ChatService.rename_window(user_id, window_id, new_title)
        if success:
            return {"message": "Chat window renamed successfully"}
        raise HTTPException(status_code=404, detail="Chat window not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))