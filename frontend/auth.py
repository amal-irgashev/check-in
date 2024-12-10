import streamlit as st
from supabase import create_client, Client 
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def init_auth():
    # Initialize session state variables if they don't exist
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    
    # Try to get stored tokens from browser storage
    try:
        # Check if there's a stored session
        session = supabase.auth.get_session()
        
        if session and session.access_token:
            # Verify and refresh the token if needed
            response = supabase.auth.get_user(session.access_token)
            if response and response.user:
                st.session_state.authenticated = True
                st.session_state.user = response.user
                st.session_state.access_token = session.access_token
                st.session_state.refresh_token = session.refresh_token
                return
            
    except Exception as e:
        logging.error(f"Auth verification failed: {str(e)}")
        _clear_session()

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    try:
        supabase.auth.sign_out()
    except Exception as e:
        logging.error(f"Error during sign out: {str(e)}")

def sign_in(email: str, password: str) -> bool:
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token
            return True
            
    except Exception as e:
        logging.error(f"Sign in error: {str(e)}")
        return False
    
    return False

def sign_up(email: str, password: str) -> bool:
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return bool(response.user)
    except Exception as e:
        logging.error(f"Sign up error: {str(e)}")
        return False

def logout_user():
    _clear_session()