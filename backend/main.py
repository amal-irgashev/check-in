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
        # Validate input
        if not entry.content.strip():
            raise HTTPException(status_code=400, detail="Journal entry content cannot be empty")

        # Save journal entry to Supabase
        entry_data = {
            "user_id": MOCK_USER_ID,
            "entry": entry.content,
            "created_at": "now()"  # Add created_at timestamp
        }
        
        try:
            entry_result = supabase.table("journal_entries").insert(entry_data).execute()
        except Exception as db_error:
            logging.error(f"Database error saving journal entry: {str(db_error)}")
            raise HTTPException(status_code=500, detail="Failed to save journal entry to database")
        
        if not entry_result.data:
            raise HTTPException(status_code=500, detail="No data returned from database")
            
        entry_id = entry_result.data[0]["id"]
        
        # Get AI analysis
        try:
            analysis = analyze_journal_entry(entry.content)
        except Exception as ai_error:
            logging.error(f"AI analysis error: {str(ai_error)}")
            # Save the entry even if analysis fails
            return {
                "status": "partial_success",
                "data": {
                    "entry": entry_result.data[0],
                    "error": "Analysis failed but entry was saved"
                }
            }
        
        # Save analysis to Supabase
        analysis_data = {
            "entry_id": entry_id,
            "mood": analysis["mood"],
            "summary": analysis["summary"],
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
                "analysis": analysis_result.data[0]
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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Journaling API!"}