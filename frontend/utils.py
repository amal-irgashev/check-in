from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
import requests
import logging
from typing import Optional, Any, Dict

load_dotenv()

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{API_BASE_URL}/api/v1"

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

def make_authenticated_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict] = None, 
    stream: bool = False
) -> Any:
    """Make an authenticated request to the API"""
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
        
    url = f"{API_URL}{endpoint}"
    
    headers = {}
    if st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=data if data else None,
            headers=headers,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            status_code = e.response.status_code
            if status_code == 401:
                st.session_state.authenticated = False
                raise Exception("User not authenticated")
            elif status_code == 404:
                raise Exception(f"Request failed: {e}")
            else:
                raise Exception(f"API error: {e}")
        else:
            raise Exception(f"Network error: {e}")

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None