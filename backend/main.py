from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import openai
from db.models import journal_entry, journal_analysis
from ai_agents.ai_analysis import analyze_journal_entry
from ai_agents.chatbot import get_chat_response
from pydantic import BaseModel
from uuid import UUID
import logging
from auth.auth import auth_middleware
from db.supabase_client import get_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8501",
]

# CORS middleware must come before auth middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add auth middleware with public endpoints
public_paths = {"/", "/docs", "/openapi.json"}

@app.middleware("http")
async def auth_middleware_with_public_paths(request: Request, call_next):
    path = request.url.path
    if path in public_paths:
        return await call_next(request)
    return await auth_middleware(request, call_next)

class JournalEntryRequest(BaseModel):
    content: str

class ChatRequest(BaseModel):
    message: str

# Analyze entry
@app.post("/analyze-entry")
async def analyze_entry(entry: JournalEntryRequest):
    try:
        analysis = analyze_journal_entry(entry.content)
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Create journal entry
@app.post("/journal-entry")
async def create_journal_entry(entry: JournalEntryRequest, request: Request):
    try:
        user_id = request.state.user.id
        logging.info(f"Creating entry for user_id: {user_id}")
        
        # Get authenticated client and set session
        supabase = get_client()
        access_token = request.state.access_token
        refresh_token = request.state.refresh_token
        
        if not refresh_token:
            # If no refresh token, try alternative session setup
            supabase.auth.set_session(access_token)
        else:
            supabase.auth.set_session(access_token, refresh_token)
        
        entry_data = {
            "entry": entry.content,
            "user_id": user_id,
            "created_at": "now()"
        }
        logging.info(f"Entry data to insert: {entry_data}")
        
        entry_result = supabase.table("journal_entries").insert(entry_data).execute()
        
        if not entry_result.data:
            raise HTTPException(status_code=500, detail="Failed to save journal entry")
            
        entry_id = entry_result.data[0]['id']
        
        # Get AI analysis
        analysis = analyze_journal_entry(entry.content)
        
        # Save analysis using same authenticated client
        analysis_data = {
            "entry_id": entry_id,
            "mood": analysis["mood"],
            "summary": analysis["summary"],
            "categories": analysis["categories"],
            "key_insights": analysis["key_insights"],
            "created_at": "now()"
        }
        
        try:
            analysis_result = supabase.table("journal_analyses").insert(analysis_data).execute()
        except Exception as analysis_db_error:
            logging.error(f"Database error saving analysis: {str(analysis_db_error)}")
            return {
                "status": "partial_success",
                "data": {
                    "entry": entry_result.data[0],
                    "analysis": analysis,
                    "error": "Analysis generated but failed to save to database"
                }
            }
        
        return {
            "status": "success",
            "data": {
                "entry": entry_result.data[0],
                "analysis": analysis
            }
        }
        
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logging.error(f"Unexpected error in create_journal_entry: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Get entries
@app.get("/entries")
async def get_entries(request: Request):
    logging.info("=== Get Entries Endpoint Start ===")
    try:
        if not hasattr(request.state, 'user') or not request.state.user:
            logging.error("No user in request state")
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = request.state.user.id
        logging.info(f"Fetching entries for user: {user_id}")
        
        # Get authenticated client
        supabase = get_client()
        
        # Get both tokens from request
        auth_header = request.headers.get('Authorization')
        refresh_token = request.headers.get('X-Refresh-Token')
        
        if not auth_header:
            raise HTTPException(status_code=401, detail="No authorization header")
            
        access_token = auth_header.split(' ')[1]
        
        # Set session with both tokens if available
        if refresh_token:
            supabase.auth.set_session(access_token, refresh_token)
        else:
            supabase.auth.set_session(access_token)
        
        # Fetch entries with error handling
        try:
            entries = supabase.table("journal_entries")\
                .select("*, journal_analyses(*)")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            logging.info(f"Entries fetched successfully: {len(entries.data) if entries.data else 0}")    
            return entries.data or []
            
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
            
    except HTTPException as http_error:
        logging.error(f"HTTP Exception in get_entries: {str(http_error)}")
        raise http_error
    except Exception as e:
        logging.error(f"Failed to fetch entries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest, request_obj: Request):
    try:
        user_id = request_obj.state.user.id
        response = get_chat_response(user_id, request.message)
        return {"response": response}
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat response")

# Root test
@app.get("/")
def read_root():
    return {"message": "API is running!"}