# AUTHENTICATION
# login
# sign up
# logout
# refresh session

import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import logging
from supabase.client import AuthApiError


# Load environment variables
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))



def init_auth():
    # Set up session state variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None 
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
        
    try:
        # Get current session
        session = supabase.auth.get_session()
        
        # Return if no valid session
        if not session or not session.access_token:
            return

        # Try to refresh the token
        try:
            refresh = supabase.auth.refresh_session()
            if refresh and refresh.session:
                st.session_state.authenticated = True
                st.session_state.user = refresh.user
                st.session_state.access_token = refresh.session.access_token
                st.session_state.refresh_token = refresh.session.refresh_token
                return
        except:
            pass



        # Verify existing token
        user = supabase.auth.get_user(session.access_token)
        if user and user.user:
            st.session_state.authenticated = True
            st.session_state.user = user.user
            st.session_state.access_token = session.access_token
            st.session_state.refresh_token = session.refresh_token
            
    except Exception as e:
        print(f"Auth error: {str(e)}")
        clear_session()

# CLEAR SESSION
def clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Sign out error: {str(e)}")
        
    st.rerun()

# REFRESH SESSION
def refresh_session():
    if not st.session_state.refresh_token:
        return False
        
    try:
        refresh = supabase.auth.refresh_session(
            refresh_token=st.session_state.refresh_token
        )
        
        if refresh and refresh.session:
            st.session_state.authenticated = True
            st.session_state.user = refresh.user
            st.session_state.access_token = refresh.session.access_token
            st.session_state.refresh_token = refresh.session.refresh_token
            return True
            
    except Exception as e:
        print(f"Refresh error: {str(e)}")
        clear_session()
        
    return False

# SIGN IN
def sign_in(email, password):
    try:
        auth = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth.user:
            st.session_state.authenticated = True
            st.session_state.user = auth.user
            st.session_state.access_token = auth.session.access_token
            st.session_state.refresh_token = auth.session.refresh_token
            return True, "Logged in!"
            
    except Exception as e:
        error = str(e)
        if "Invalid login" in error:
            return False, "Wrong email/password"
        if "Email not confirmed" in error:
            return False, "Please confirm your email"
        print(f"Login error: {error}")
        return False, "Login failed"
    
    return False, "Login failed"



# SIGN UP
def sign_up(email, password):
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        return False, "Missing config"

    try:
        auth = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {}}
        })
        # If user is created, set session state
        if auth.user:
            if auth.session:
                st.session_state.authenticated = True
                st.session_state.user = auth.user
                st.session_state.access_token = auth.session.access_token
                st.session_state.refresh_token = auth.session.refresh_token
                return True, "Account created!"
            return True, "Check email to confirm"
                
        return False, "Sign up failed"
        
    except AuthApiError as e:
        error = str(e).lower()
        if "already registered" in error:
            return False, "Email already exists"
        if "password" in error:
            return False, "Password too short"
        if "valid email" in error:
            return False, "Invalid email"
        
        print(f"Sign up error: {str(e)}")
        return False, "Sign up failed"
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False, "Error occurred"

def logout_user():
    clear_session()