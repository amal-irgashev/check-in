import streamlit as st
from datetime import datetime
import requests

# Assume make_authenticated_request is defined elsewhere
from utils import make_authenticated_request

# Set page config
st.set_page_config(page_title="User Profile", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
    }
    .stat-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-2px);
    }
    .activity-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #eee;
        transition: background-color 0.2s;
    }
    .activity-item:hover {
        background-color: #f8f9fa;
        padding-left: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def display_user_info(user):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Personal Details")
        st.write(f"📧 Email: {user.email}")
    
    with col2:
        st.subheader("Edit Profile")
        name = st.text_input("Full Name", 
                            value=user.user_metadata.get('full_name', ''),
                            placeholder="Enter your full name")
        
        if st.button("Update Profile", type="primary"):
            try:
                make_authenticated_request(
                    "POST", 
                    "api/profile/update",
                    {"full_name": name}
                )
                st.success("Profile updated successfully!")
            except Exception as e:
                st.error(f"Update failed: {str(e)}")

def display_stats(stats):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Total Entries", stats.get('total_entries', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Days Active", stats.get('days_active', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Entries/Week", f"{stats.get('avg_entries_per_week', 0):.1f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    member_since = datetime.fromisoformat(stats.get('member_since', '').replace('Z', '+00:00')).strftime('%B %d, %Y') if stats.get('member_since') else 'N/A'
    st.info(f"🎉 Member Since: {member_since}")

def display_recent_activity(activities):
    st.subheader("Recent Activity")
    for activity in activities:
        st.markdown(f'<div class="activity-item">• {activity}</div>', unsafe_allow_html=True)

def main():
    st.title("👤 User Profile")

    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("🔒 Please log in to view your profile")
        return

    user = st.session_state.user
    
    with st.container():
        display_user_info(user)
    
    try:
        stats = make_authenticated_request("GET", "api/profile/stats")
        
        with st.container():
            st.subheader("📊 Statistics")
            display_stats(stats)
        
        if stats.get('recent_activity'):
            with st.container():
                display_recent_activity(stats['recent_activity'])
                
    except Exception as e:
        st.error(f"❌ Unable to load statistics: {str(e)}")

if __name__ == "__main__":
    main()