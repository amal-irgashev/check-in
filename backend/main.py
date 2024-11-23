from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from ai_agent import analyze_journal_entry
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JournalEntryRequest(BaseModel):
    content: str

MOCK_USER_ID = "d2aa1300-0d4d-4588-a0f9-5c37c9e9f89e"

@app.post("/analyze-entry")
async def analyze_entry(entry: JournalEntryRequest):
    try:
        analysis = analyze_journal_entry(entry.content)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/journal-entry")
async def create_journal_entry(entry: JournalEntryRequest):
    # Validate input
    if not entry.content.strip():
        raise HTTPException(status_code=400, detail="Journal entry content cannot be empty")

    try:
        # Save journal entry
        entry_data = {
            "user_id": MOCK_USER_ID,
            "entry": entry.content,
            "created_at": "now()"
        }
        entry_result = supabase.table("journal_entries").insert(entry_data).execute()
        
        if not entry_result.data:
            raise HTTPException(status_code=500, detail="No data returned from database")
        
        entry_id = entry_result.data[0]["id"]
        
        # Get AI analysis
        try:
            analysis = analyze_journal_entry(entry.content)
            
            # Save analysis
            analysis_data = {
                "entry_id": entry_id,
                "mood": analysis["mood"],
                "summary": analysis["summary"],
                "created_at": "now()"
            }
            analysis_result = supabase.table("journal_analyses").insert(analysis_data).execute()
            
            return {
                "status": "success",
                "data": {
                    "entry": entry_result.data[0],
                    "analysis": analysis_result.data[0]
                }
            }
            
        except Exception as analysis_error:
            logging.error(f"Analysis error: {str(analysis_error)}")
            return {
                "status": "partial_success",
                "data": {
                    "entry": entry_result.data[0],
                    "error": "Analysis failed but entry was saved"
                }
            }
            
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process journal entry")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Journaling API!"}