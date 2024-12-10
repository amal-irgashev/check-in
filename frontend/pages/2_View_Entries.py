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
        # Construct query parameters
        params = {}
        if search_term:
            params['search'] = search_term
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
            
        # Fetch entries from API using authenticated request with query parameters
        response = make_authenticated_request("GET", "entries", params=params)
        entries = response

        def delete_entry(entry_id: str):
            try:
                response = make_authenticated_request("DELETE", f"entries/{entry_id}")
                
                if response and response.get("status") == "success":
                    st.success("Entry deleted successfully!")
                    # Clear all relevant state
                    st.session_state.pop(f"confirm_delete_{entry_id}", None)
                    st.session_state.pop('entries', None)  # Clear entries cache
                    # Force an immediate rerun of the app
                    st.rerun()
                else:
                    st.error("Failed to delete entry")
            except Exception as e:
                st.error(f"Error deleting entry: {str(e)}")

        if entries:
            for entry in entries:
                try:
                    entry_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00')).strftime('%B %d, %Y %I:%M %p')
                    
                    with st.expander(f"Entry from {entry_date}"):
                        # Add delete button in a more prominent position
                        delete_key = f"delete_{entry['id']}"
                        confirm_key = f"confirm_delete_{entry['id']}"
                        
                        # Right-aligned delete button with more space
                        col1, col2 = st.columns([0.8, 0.2])
                        with col2:
                            # Make delete button more visible with custom styling
                            if st.button("🗑️ Delete Entry", key=delete_key, help="Delete this entry", type="secondary", use_container_width=True):
                                st.session_state[confirm_key] = True
                        
                        # Show confirmation dialog if needed
                        if st.session_state.get(confirm_key, False):
                            st.markdown("---")
                            st.warning("⚠️ Are you sure you want to delete this entry?")
                            col3, col4, col5 = st.columns([0.4, 0.3, 0.3])
                            with col4:
                                if st.button("✔️ Yes, Delete", key=f"yes_{entry['id']}", type="primary", use_container_width=True):
                                    delete_entry(entry['id'])
                            with col5:
                                if st.button("❌ Cancel", key=f"no_{entry['id']}", type="secondary", use_container_width=True):
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                        
                        st.markdown("---")
                        # Display entry content
                        st.write(entry['entry'])
                        
                        # Check if analysis exists and display it
                        if entry.get('journal_analyses') and len(entry['journal_analyses']) > 0:
                            analysis = entry['journal_analyses'][0]
                            st.markdown("---")
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
