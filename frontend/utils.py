from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
import requests
import logging

load_dotenv()

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def get_auth_headers():
    """Get authentication headers for API requests"""
    if not st.session_state.authenticated or not st.session_state.access_token:
        logging.error("No authentication token found in session state")
        _clear_session()
        raise Exception("User not authenticated")
        
    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }
    
    if st.session_state.refresh_token:
        headers["X-Refresh-Token"] = st.session_state.refresh_token
        
    return headers

def handle_request_error(error: requests.exceptions.RequestException):
    """Handle request errors and authentication failures"""
    logging.error(f"Request error: {str(error)}")
    
    if hasattr(error, 'response'):
        logging.error(f"Response status: {error.response.status_code}")
        logging.error(f"Response body: {error.response.text}")
        
        if error.response.status_code == 401:
            _clear_session()
            raise Exception("Authentication expired. Please log in again.")
            
    raise Exception(f"Request failed: {str(error)}")

def make_authenticated_request(method: str, endpoint: str, data: dict = None, stream: bool = False):
    """Make an authenticated request to the backend API"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        headers = get_auth_headers()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, stream=stream)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, stream=stream)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        if stream:
            return response
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        handle_request_error(e)

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None