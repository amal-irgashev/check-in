from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
import requests
import logging

load_dotenv()

def make_authenticated_request(method, endpoint, data=None):
    """
    Make an authenticated request to the backend API
    """
    if not st.session_state.authenticated or not st.session_state.access_token:
        logging.error("No authentication token found in session state")
        _clear_session()
        raise Exception("User not authenticated")
    
    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }
    
    # Add refresh token if available
    if st.session_state.refresh_token:
        headers["X-Refresh-Token"] = st.session_state.refresh_token
    
    api_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    full_url = f"{api_url}/{endpoint.lstrip('/')}"
    
    try:
        if method == "GET":
            response = requests.get(full_url, headers=headers)
        elif method == "POST":
            response = requests.post(full_url, json=data, headers=headers)
        
        if response.status_code == 401:
            _clear_session()
            raise Exception("Authentication expired. Please log in again.")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        if hasattr(e, 'response'):
            logging.error(f"Response status: {e.response.status_code}")
            logging.error(f"Response body: {e.response.text}")
            
            if e.response.status_code == 401:
                _clear_session()
                raise Exception("Authentication expired. Please log in again.")
        raise Exception(f"Request failed: {str(e)}")

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None