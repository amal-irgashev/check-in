import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create a single shared instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def verify_database_connection():
    try:
        # Try a simple query to verify database connection
        result = supabase.table('_dummy_').select('*').limit(1).execute()
        return True
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        return False

def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise Exception("Supabase configuration missing")
    return supabase