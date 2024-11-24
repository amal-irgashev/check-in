import streamlit as st
from auth import init_supabase, login, signup, logout, get_current_user
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
import logging

# Initialize Supabase client
supabase = init_supabase()

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

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

# Authentication UI
if not st.session_state.user:
    st.title("Welcome to Smart Journal 📔")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if login(supabase, email, password):
                    st.rerun()
    
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    if signup(supabase, new_email, new_password):
                        st.info("Please check your email to verify your account before logging in.")
    
    st.stop()

# Main app UI (only shown when logged in)
st.sidebar.title(f"Welcome, {st.session_state.user.email}")
if st.sidebar.button("Logout"):
    logout(supabase)
    st.rerun()

# Navigation
page = st.sidebar.radio(
    "Navigate to",
    ["New Entry", "View Entries", "AI Insights"]
)

# API endpoint (replace with your actual backend URL)
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
                    json={
                        "content": entry_content,
                        "user_id": st.session_state.user.id
                    },
                    headers={
                        "Authorization": f"Bearer {st.session_state.session.access_token}"
                    }
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
            # Fetch entries from Supabase
            query = supabase.table('journal_entries').select('''
                *,
                journal_analyses (
                    mood,
                    summary,
                    key_insights
                )
            ''')
            
            # Apply date filters if selected
            if start_date:
                query = query.gte('created_at', f"{start_date.isoformat()}T00:00:00")
            if end_date:
                query = query.lte('created_at', f"{end_date.isoformat()}T23:59:59")
                
            # Apply search filter if provided
            if search_term:
                query = query.ilike('entry', f'%{search_term}%')
                
            # Order by date descending
            query = query.order('created_at', desc=True)
            
            # Execute query
            response = query.execute()
            entries = response.data

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
                            
                            # Add edit and delete buttons
                            col1, col2 = st.columns([1, 10])
                            with col1:
                                if st.button('Delete', key=f"delete_{entry['id']}"):
                                    try:
                                        # Delete from journal_entries (cascade will handle analyses)
                                        supabase.table('journal_entries').delete().eq('id', entry['id']).execute()
                                        st.success("Entry deleted successfully!")
                                        st.rerun()
                                    except Exception as delete_error:
                                        st.error(f"Failed to delete entry: {str(delete_error)}")
                    except Exception as e:
                        st.error(f"Error formatting entry: {str(e)}")
            else:
                st.info("No entries found for the selected criteria.")
                
        except Exception as e:
            st.error(f"Failed to load entries: {str(e)}")
            logging.error(f"Error in View Entries: {str(e)}")

elif page == "AI Insights":
    st.title("AI Insights Dashboard")
    
    # Time period selector
    time_period = st.selectbox(
        "Select Time Period",
        ["Last Week", "Last Month", "Last 3 Months", "Last Year"]
    )
    
    # Create columns for different metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mood Trends")
        # Add a placeholder chart for mood trends
        st.line_chart(pd.DataFrame({'mood': [1, 2, 3, 2, 4, 3, 2]}))
        
    with col2:
        st.subheader("Common Themes")
        # Add a placeholder chart for common themes
        st.bar_chart(pd.DataFrame({
            'themes': [10, 20, 15, 25, 30]
        }))
    
    # Display key insights
    st.subheader("Key Insights")
    with st.expander("View Detailed Insights"):
        st.write("• Your mood tends to be more positive on weekends")
        st.write("• Most productive journaling time: Evening")
        st.write("• Common topics: work, family, personal growth")
