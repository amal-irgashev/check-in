# PROFILE PAGE
# display user profile
# display user stats
# display user entries
# display user chats

import streamlit as st
from datetime import datetime
from utils import make_authenticated_request

st.title("👤 User Profile")

if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in to view your profile")
else:
    user = st.session_state.user
    
    # Display user info
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Personal Details") 
        st.write(f"📧 Email: {user.email}")
    
    with col2:
        st.subheader("Edit Profile")
        name = st.text_input("Full Name", 
                            value=user.user_metadata.get('full_name', ''),
                            placeholder="Enter your full name")
        
        if st.button("Update Profile"):
            try:
                make_authenticated_request("POST", "api/profile/update", {"full_name": name})
                st.success("Profile updated successfully!")
            except Exception as e:
                st.error(f"Update failed: {str(e)}")

    # Display stats
    try:
        stats = make_authenticated_request("GET", "api/profile/stats")
        
        st.subheader("📊 Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", stats.get('total_entries', 0))
        with col2:
            st.metric("Days Active", stats.get('days_active', 0))
        with col3:
            st.metric("Entries/Week", f"{stats.get('avg_entries_per_week', 0):.1f}")
        
        member_since = datetime.fromisoformat(stats.get('member_since', '').replace('Z', '+00:00')).strftime('%B %d, %Y') if stats.get('member_since') else 'N/A'
        st.info(f"🎉 Member Since: {member_since}")

        # Display recent activity
        if stats.get('recent_activity'):
            st.subheader("Recent Activity")
            for activity in stats['recent_activity']:
                st.write(f"• {activity}")
                
    except Exception as e:
        st.error(f"❌ Unable to load statistics: {str(e)}")