import streamlit as st
import requests
from datetime import datetime
from auth import init_auth
from utils import make_authenticated_request
init_auth()

st.title("Create New Journal Entry")

# API endpoint
API_URL = "http://localhost:8000"

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
            response = make_authenticated_request(
                "POST",
                "journal-entry",
                {"content": entry_content}
            )
            if response.get("status") == "success":
                st.success("Entry saved successfully!")
                if "data" in response and "analysis" in response["data"]:
                    analysis = response["data"]["analysis"]
                    with st.expander("View AI Analysis"):
                        st.write("**Mood:**", analysis.get("mood", "N/A"))
                        st.write("**Summary:**", analysis.get("summary", "N/A"))
                        st.write("**Categories:**", analysis.get("categories", "N/A"))
                        st.write("**Key Insights:**", analysis.get("key_insights", "N/A"))
            else:
                st.error("Failed to save entry")
        except Exception as e:
            if "User not authenticated" in str(e):
                st.error("Please log in to save entries")
            else:
                st.error(f"An error occurred: {str(e)}")
