import streamlit as st
from supabase import create_client, Client 
import os
from dotenv import load_dotenv
import logging
import datetime
from supabase.client import AuthApiError, AuthInvalidCredentialsError

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
    
    try:
        # Check if there's a stored session
        session = supabase.auth.get_session()
        
        if session and session.access_token:
            try:
                # Try to refresh the token first
                refresh_response = supabase.auth.refresh_session()
                if refresh_response and refresh_response.session:
                    st.session_state.authenticated = True
                    st.session_state.user = refresh_response.user
                    st.session_state.access_token = refresh_response.session.access_token
                    st.session_state.refresh_token = refresh_response.session.refresh_token
                    return
                
                # Fallback to verifying current token if refresh fails
                user_response = supabase.auth.get_user(session.access_token)
                if user_response and user_response.user:
                    st.session_state.authenticated = True
                    st.session_state.user = user_response.user
                    st.session_state.access_token = session.access_token
                    st.session_state.refresh_token = session.refresh_token
                    return
                
            except Exception as e:
                if "token expired" in str(e).lower() or "invalid token" in str(e).lower():
                    logging.info("Token expired, clearing session")
                    _clear_session()
                else:
                    logging.error(f"Error refreshing/verifying token: {str(e)}")
                    _clear_session()
                
    except Exception as e:
        logging.error(f"Auth initialization failed: {str(e)}")
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
    st.rerun()

def refresh_session():
    """Attempt to refresh the current session"""
    try:
        if st.session_state.refresh_token:
            # Explicitly pass the refresh token
            response = supabase.auth.refresh_session(
                refresh_token=st.session_state.refresh_token
            )
            if response and response.session:
                st.session_state.authenticated = True
                st.session_state.user = response.user
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
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
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token
            return True, "Successfully logged in!"
            
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return False, "Invalid email or password."
        elif "Email not confirmed" in error_msg:
            return False, "Please confirm your email address before logging in."
        else:
            logging.error(f"Sign in error: {error_msg}")
            return False, "An error occurred during sign in. Please try again."
    
    return False, "Login failed. Please check your credentials."

def sign_up(email: str, password: str) -> tuple[bool, str]:
    try:
        # Verify Supabase configuration
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            logging.error("Missing Supabase configuration")
            return False, "Service configuration error. Please contact support."

        # Add logging to debug the request
        logging.info(f"Attempting to sign up user with email: {email}")
        
        # Test connection with a simple auth call
        try:
            supabase.auth.get_session()
            logging.info("Supabase connection verified")
        except Exception as conn_e:
            logging.error(f"Supabase connection error: {str(conn_e)}")
            return False, "Unable to connect to authentication service"
        
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {}  # Include empty data object to ensure proper initialization
            }
        })
        
        if response.user:
            if response.session:  # Auto-confirm is enabled
                st.session_state.authenticated = True
                st.session_state.user = response.user
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                return True, "Account created successfully!"
            else:  # Email confirmation required
                return True, "Please check your email to confirm your account."
                
        logging.error(f"Sign up failed with response: {response}")
        return False, "Failed to create account. Please try again."
        
    except AuthApiError as e:
        error_msg = str(e)
        logging.error(f"Auth API error during sign up: {error_msg}")
        
        # Log additional details about the error
        if hasattr(e, 'status'):
            logging.error(f"Error status code: {e.status}")
        if hasattr(e, 'code'):
            logging.error(f"Error code: {e.code}")
            
        if "already registered" in error_msg.lower():
            return False, "This email is already registered."
        elif "password" in error_msg.lower():
            return False, "Password must be at least 6 characters long."
        elif "valid email" in error_msg.lower():
            return False, "Please enter a valid email address."
        elif "database error" in error_msg.lower():
            # Log additional debugging information
            logging.error("Database error details:", exc_info=True)
            return False, "Unable to create account at this time. Please try again later."
        
        logging.error(f"Detailed auth error: {error_msg}", exc_info=True)
        return False, "Sign up failed. Please try again later."
        
    except Exception as e:
        logging.error(f"Unexpected error during sign up: {str(e)}", exc_info=True)
        return False, "An unexpected error occurred. Please try again later."

def logout_user():
    _clear_session()