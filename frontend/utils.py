from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
import requests
import logging
from typing import Optional, Any, Dict

load_dotenv()

API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def make_authenticated_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict] = None, 
    stream: bool = False
) -> Any:
    """Make an authenticated request to the API with token refresh handling"""
    if not st.session_state.get("authenticated"):
        raise Exception("User not authenticated")
        
    if not st.session_state.get("access_token"):
        raise Exception("No authentication token found")
    
    # Clean up endpoint
    endpoint = endpoint.strip('/')
    if endpoint.startswith('http'):
        # If it's a full URL, use it as is
        url = endpoint
    else:
        # Otherwise, combine with base URL
        url = f"{API_BASE_URL}/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {st.session_state.access_token}",
        "Content-Type": "application/json"
    }
    
    if st.session_state.get("refresh_token"):
        headers["X-Refresh-Token"] = st.session_state.refresh_token
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None,
            stream=stream
        )
        
        # Handle token expiration
        if response.status_code == 401:
            logging.info("Received 401, attempting token refresh...")
            from auth import refresh_session, _clear_session
            
            if refresh_session():
                # Update headers with new token and retry request
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

def _clear_session():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None