# NEW ENTRY PAGE
# create a new journal entry
# analyze the entry with AI
# save the entry to the database


import streamlit as st
from datetime import datetime
from auth import init_auth
from utils import make_authenticated_request

API_URL = "http://localhost:8000"

init_auth()

st.title("✍️ Create New Journal Entry")

with st.form("journal_entry_form"):
    # Date picker with default to today
    entry_date = st.date_input("Date", datetime.now())

    # Journal entry text area
    entry_content = st.text_area(
        "What's on your mind?",
        placeholder="Start writing your journal entry here...",
        height=300
    )

    # SUBMIT button
    submit_button = st.form_submit_button("Save Entry")

    if submit_button:
        if not entry_content:
            st.error("Please write something before saving.")
            st.stop()
            
        try:
            # First analyze the entry
            analysis = make_authenticated_request(
                "POST",
                "analyze-entry",
                {"content": entry_content}
            )
            
            # Then create the journal entry
            # Save the entry to the database
            response = make_authenticated_request(
                "POST", 
                "journal-entry",
                {"content": entry_content}
            )
            
            # Check if save was successful
            if response and response.get("status") == "success":
                st.success("Your entry was saved! 🎉")
                
                
                
                # Get the AI analysis if available
                response_data = response.get("data", {})
                analysis_data = response_data.get("analysis", {})
                
                
                
                # Show the analysis in an expandable section
                with st.expander("View AI Analysis", expanded=True):
                    st.markdown(":orange[**Mood:**] " + analysis_data.get("mood", "N/A")) 
                    st.markdown(":orange[**Summary:**] " + analysis_data.get("summary", "N/A"))
                    st.markdown(":orange[**Key Insights:**] " + analysis_data.get("key_insights", "N/A"))
            else:
                st.error("Something went wrong saving your entry. Try again?")
                
        except Exception as e:
            # Handle common errors
            error_msg = str(e)
            if "User not authenticated" in error_msg:
                st.error("You need to log in first!")
            else:
                st.error("Oops, something went wrong!")
                print(f"Error details: {error_msg}")  # For debugging