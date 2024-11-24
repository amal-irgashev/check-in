import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import logging

# Configure page settings
st.set_page_config(
    page_title="Smart Journal",
    page_icon="📔",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextArea textarea {
        height: 300px;
    }
    </style>
""", unsafe_allow_html=True)

# Navigation
page = st.sidebar.radio(
    "Navigate to",
    ["New Entry", "View Entries"]
)

# API endpoint
API_URL = "http://localhost:8000"

if page == "New Entry":
    st.title("Create New Journal Entry")
    
    with st.form("journal_entry_form"):
        # Date picker with default to today
        entry_date = st.date_input("Date", datetime.now())
        
        # Journal entry text area
        entry_content = st.text_area(
            "What's on your mind?",
            placeholder="Start writing your journal entry here..."
        )
        
        # Submit button
        submit_button = st.form_submit_button("Save Entry")
        
        if submit_button and entry_content:
            try:
                response = requests.post(
                    f"{API_URL}/journal-entry",
                    json={"content": entry_content}
                )
                if response.status_code == 200:
                    st.success("Entry saved successfully!")
                    response_data = response.json()
                    if "data" in response_data and "analysis" in response_data["data"]:
                        analysis = response_data["data"]["analysis"]
                        with st.expander("View AI Analysis"):
                            st.write("**Mood:**", analysis.get("mood", "N/A"))
                            st.write("**Summary:**", analysis.get("summary", "N/A"))
                else:
                    st.error(f"Failed to save entry: {response.text}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

elif page == "View Entries":
    st.title("Journal Entries")
    
    # Date range filters
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From")
    with col2:
        end_date = st.date_input("To")
    
    # Search and filters
    search_term = st.text_input("Search entries", placeholder="Enter keywords...")
    
    # Add loading state
    with st.spinner("Loading entries..."):
        try:
            # Fetch entries from API
            response = requests.get(f"{API_URL}/entries")
            entries = response.json()

            if entries:
                for entry in entries:
                    # Format the date for display
                    try:
                        entry_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00')).strftime('%B %d, %Y %I:%M %p')
                        
                        with st.expander(f"Entry from {entry_date}"):
                            st.write(entry['entry'])
                            
                            # Check if analysis exists and display it
                            if entry.get('journal_analyses') and len(entry['journal_analyses']) > 0:
                                analysis = entry['journal_analyses'][0]
                                st.write("**Mood:**", analysis.get('mood', 'N/A'))
                                st.write("**Summary:**", analysis.get('summary', 'N/A'))
                                if analysis.get('key_insights'):
                                    st.write("**Key Insights:**", analysis['key_insights'])
                    except Exception as e:
                        st.error(f"Error formatting entry: {str(e)}")
            else:
                st.info("No entries found for the selected criteria.")
                
        except Exception as e:
            st.error(f"Failed to load entries: {str(e)}")
            logging.error(f"Error in View Entries: {str(e)}")
