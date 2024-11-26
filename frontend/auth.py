import streamlit as st
from backend.db.supabase_client import get_client
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = get_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def init_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    
    # Verify existing token if present
    if st.session_state.access_token:
        try:
            response = supabase.auth.get_user(st.session_state.access_token)
            if response and response.user:
                st.session_state.authenticated = True
                st.session_state.user = response.user
            else:
                _clear_session()
        except Exception as e:
            logging.error(f"Auth verification failed: {str(e)}")
            _clear_session()

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None

def login_user(email: str, password: str):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.user = response.user
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token
        st.session_state.authenticated = True
        
        logging.info(f"Login successful for user: {response.user.email}")
        logging.info(f"Access token received: {response.session.access_token[:10]}...")
        
        return True
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return False

def signup_user(email: str, password: str):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        st.success("Sign up successful! Please check your email to verify your account.")
        return True
    except Exception as e:
        st.error(f"Sign up failed: {str(e)}")
        return False

def logout_user():
    try:
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user = None
        st.success("Logged out successfully!")
    except Exception as e:
        st.error(f"Logout failed: {str(e)}")