from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
import requests
import logging
from typing import Optional, Dict, Any

load_dotenv()

# URL for backend API
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000") 


# MAKE AUTHENTICATED REQUEST
def make_authenticated_request(method: str, endpoint: str, data: Optional[Dict] = None, stream: bool = False) -> Any:
    """Makes API requests with auth token"""
    # Check if user is logged in
    if not st.session_state.get("authenticated"):
        raise Exception("User not authenticated")
        
    if not st.session_state.get("access_token"):
        raise Exception("No authentication token found")
    
    # Format the URL
    endpoint = endpoint.strip('/')
    url = endpoint if endpoint.startswith('http') else f"{API_BASE_URL}/{endpoint}"
    
    # Set up request headers
    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }
    
    if st.session_state.get("refresh_token"):
        headers["X-Refresh-Token"] = st.session_state.refresh_token
    
    try:
        # Make the API request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None,
            stream=stream
        )
        
        # Try to refresh token if expired
        if response.status_code == 401:
            from auth import refresh_session, _clear_session
            
            if refresh_session():
                # Try request again with new token
                headers["Authorization"] = f"Bearer {st.session_state.access_token}"
                if st.session_state.get("refresh_token"):
                    headers["X-Refresh-Token"] = st.session_state.refresh_token
                
                response = requests.request(
                    method=method,
                    url=url, 
                    headers=headers,
                    json=data if data else None,
                    stream=stream
                )
            else:
                _clear_session()
                raise Exception("Session expired. Please log in again.")
                
        response.raise_for_status()
        return response.json() if not stream else response
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        raise Exception(f"API request failed: {str(e)}")

# CLEAR SESSION ?
def _clear_session():
    """Reset all session state variables"""
    st.session_state.authenticated = False 
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None