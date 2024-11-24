from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import openai
from db.models import journal_entry, journal_analysis
from ai_agent import analyze_journal_entry
from pydantic import BaseModel
from uuid import UUID
import logging

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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JournalEntryRequest(BaseModel):
    content: str

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

MOCK_USER_ID = "d2aa1300-0d4d-4588-a0f9-5c37c9e9f89e"

@app.post("/journal-entry")
async def create_journal_entry(entry: JournalEntryRequest):
    try:
        # Save entry to Supabase
        entry_data = {
            "entry": entry.content,  # Changed from 'content' to 'entry'
            "user_id": MOCK_USER_ID,
            "created_at": "now()"
        }
        
        entry_result = supabase.table("journal_entries").insert(entry_data).execute()
        
        if not entry_result.data:
            raise HTTPException(status_code=500, detail="Failed to save journal entry")
            
        entry_id = entry_result.data[0]['id']
        
        # Get AI analysis
        analysis = analyze_journal_entry(entry.content)
        
        # Save analysis to Supabase
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

@app.get("/entries")
async def get_entries():
    try:
        entries = supabase.table("journal_entries")\
            .select("*, journal_analyses(*)").execute()
        return entries.data
    except Exception as e:
        logging.error(f"Failed to fetch entries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch entries")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Journaling API!"}