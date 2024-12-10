# VIEW ENTRIES PAGE
# view all journal entries
# add date filters
# add search box
# add delete button

import streamlit as st
from datetime import datetime
import logging

from auth import init_auth
from utils import make_authenticated_request

# Make sure user is logged in before showing anything
init_auth()

st.title("📝 Journal Entries")


# add some date filters to narrow down entries
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("From")
with col2:
    end_date = st.date_input("To")

# Add a search box to find specific entries
search_term = st.text_input("Search entries", placeholder="Enter keywords...")




# Show a loading spinner while we fetch the entries
with st.spinner("Loading entries..."):
    try:
        # Build up our search filters
        query_params = []
        if search_term:
            query_params.append(f"search={search_term}")
        if start_date:
            query_params.append(f"start_date={start_date.isoformat()}")
        if end_date:
            query_params.append(f"end_date={end_date.isoformat()}")
            
            
        # Put together the API endpoint
        endpoint = "entries"
        if query_params:
            endpoint += "?" + "&".join(query_params)
            
        # Get entries from our backend
        response = make_authenticated_request("GET", endpoint)
        entries = response
        
        

        # Helper function to delete entries
        def delete_entry(entry_id: str):
            try:
                response = make_authenticated_request(
                    "DELETE",
                    f"/entries/{entry_id}"
                )
                
                if response and response.get("status") == "success":
                    st.success("Entry deleted successfully!")
                    # Clean up our state
                    st.session_state.pop(f"confirm_delete_{entry_id}", None)
                    st.session_state.pop('entries', None)  # Clear entries cache
                    # Refresh the page
                    st.rerun()
                else:
                    st.error("Failed to delete entry")
            except Exception as e:
                st.error(f"Error deleting entry: {str(e)}")
                
                
                
                
        # Show all our entries in a nice list
        if entries:
            for entry in entries:
                try:
                    # Format the date nicely
                    entry_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00')).strftime('%B %d, %Y %I:%M %p')
                    
                    with st.expander(f"Entry from {entry_date}"):
                        # Set up our delete button stuff
                        delete_key = f"delete_{entry['id']}"
                        confirm_key = f"confirm_delete_{entry['id']}"
                        
                        
                        
                        # Put delete button on the right
                        col1, col2 = st.columns([0.8, 0.2])
                        with col2:
                            if st.button("Delete", key=delete_key, help="Delete this entry", type="secondary", use_container_width=True):
                                st.session_state[confirm_key] = True
                                
                                
                        
                        # Double check before deleting
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
                        # Show the actual journal entry
                        st.write(entry['entry'])
                        
                        # Show the AI analysis if we have it
                        if entry.get('journal_analyses') and len(entry['journal_analyses']) > 0:
                            analysis = entry['journal_analyses'][0]
                            st.markdown("---")
                            st.markdown(":orange[**Mood:**] " + analysis.get('mood', 'N/A'))
                            st.markdown(":orange[**Summary:**] " + analysis.get('summary', 'N/A'))
                            if analysis.get('key_insights'):
                                st.markdown(":orange[**Key Insights:**] " + analysis['key_insights'])
                except Exception as e:
                    st.error(f"Error formatting entry: {str(e)}")
        else:
            st.info("No entries found for the selected criteria.")
            
    except Exception as e:
        # Oops, something went wrong
        if "User not authenticated" in str(e):
            st.error("Please log in to view entries")
        else:
            st.error(f"Failed to load entries: {str(e)}")
            logging.error(f"Error in View Entries: {str(e)}")
