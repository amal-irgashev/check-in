import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# create a db client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# get the client
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise Exception("Supabase configuration missing")
    return supabase