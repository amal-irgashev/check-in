from supabase import create_client
import streamlit as st
from typing import Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

def init_supabase():
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

def login(supabase, email: str, password: str) -> bool:
    try:
        # Authenticate with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise Exception("Invalid credentials")
        
        # Store both user and session data
        st.session_state.user = auth_response.user
        st.session_state.session = auth_response.session
        return True
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        st.error(f"Login failed: {str(e)}")
        return False

def signup(supabase, email: str, password: str) -> bool:
    try:
        # Create auth user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not response.user:
            raise Exception("Failed to create user")
            
        # The trigger will automatically create the user record in our users table
        st.success("Signup successful! Please check your email to verify your account.")
        return True
        
    except Exception as e:
        logging.error(f"Signup error: {str(e)}")
        st.error(f"Signup failed: {str(e)}")
        return False

def logout(supabase):
    try:
        supabase.auth.sign_out()
        st.session_state.user = None
    except Exception as e:
        st.error(f"Logout failed: {str(e)}")

def get_current_user():
    return st.session_state.get('user', None)