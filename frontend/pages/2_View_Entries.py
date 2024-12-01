import streamlit as st
from datetime import datetime
import logging

from auth import init_auth
from utils import make_authenticated_request

init_auth()

st.title("📝 Journal Entries")

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
        # Fetch entries from API using authenticated request
        response = make_authenticated_request("GET", "entries")
        entries = response

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
        if "User not authenticated" in str(e):
            st.error("Please log in to view entries")
        else:
            st.error(f"Failed to load entries: {str(e)}")
            logging.error(f"Error in View Entries: {str(e)}")
