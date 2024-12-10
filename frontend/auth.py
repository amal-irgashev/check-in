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
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            if response.user.confirmed_at:
                # User is automatically confirmed
                return True, "Account created successfully!"
            else:
                # Email confirmation required
                return True, "Please check your email to confirm your account."
        return False, "Failed to create account."
        
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg:
            return False, "This email is already registered."
        elif "Password should be at least" in error_msg:
            return False, "Password is too weak. Please use a stronger password."
        elif "Invalid email" in error_msg:
            return False, "Please enter a valid email address."
        else:
            logging.error(f"Sign up error: {error_msg}")
            return False, "An error occurred during sign up. Please try again."

def logout_user():
    _clear_session()