import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from supabase.client import AuthApiError

# Load environment variables and initialize client
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def init_auth():
    # Initialize session state
    for key in ['authenticated', 'user', 'access_token', 'refresh_token']:
        if key not in st.session_state:
            st.session_state[key] = None
    st.session_state.authenticated = False
    
    try:
        session = supabase.auth.get_session()
        if not session or not session.access_token:
            return

        # Try refreshing token first
        try:
            refresh_response = supabase.auth.refresh_session()
            if refresh_response and refresh_response.session:
                _update_session(refresh_response)
                return
        except:
            pass

        # Verify current token as fallback
        user_response = supabase.auth.get_user(session.access_token)
        if user_response and user_response.user:
            st.session_state.authenticated = True
            st.session_state.user = user_response.user
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            
    except Exception as e:
        logging.error(f"Auth initialization failed: {str(e)}")
        _clear_session()

def _update_session(response):
    st.session_state.authenticated = True
    st.session_state.user = response.user
    st.session_state.access_token = response.session.access_token
    st.session_state.refresh_token = response.session.refresh_token

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    try:
        supabase.auth.sign_out()
    except Exception as e:
        logging.error(f"Error during sign out: {str(e)}")
    st.rerun()

def refresh_session():
    try:
        if st.session_state.refresh_token:
            response = supabase.auth.refresh_session(
                refresh_token=st.session_state.refresh_token
            )
            if response and response.session:
                _update_session(response)
                return True
    except Exception as e:
        logging.error(f"Session refresh failed: {str(e)}")
        _clear_session()
    return False

def sign_in(email: str, password: str) -> tuple[bool, str]:
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        if response.user:
            _update_session(response)
            return True, "Successfully logged in!"
            
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return False, "Invalid email or password."
        elif "Email not confirmed" in error_msg:
            return False, "Please confirm your email address before logging in."
        logging.error(f"Sign in error: {error_msg}")
        return False, "An error occurred during sign in. Please try again."
    
    return False, "Login failed. Please check your credentials."

def sign_up(email: str, password: str) -> tuple[bool, str]:
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        return False, "Service configuration error. Please contact support."

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {}}
        })
        
        if response.user:
            if response.session:
                _update_session(response)
                return True, "Account created successfully!"
            return True, "Please check your email to confirm your account."
                
        return False, "Failed to create account. Please try again."
        
    except AuthApiError as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg:
            return False, "This email is already registered."
        elif "password" in error_msg:
            return False, "Password must be at least 6 characters long."
        elif "valid email" in error_msg:
            return False, "Please enter a valid email address."
        
        logging.error(f"Auth API error: {str(e)}")
        return False, "Sign up failed. Please try again later."
        
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return False, "An unexpected error occurred. Please try again later."

def logout_user():
    _clear_session()