import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create a single shared instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_client() -> Client:
    return supabase