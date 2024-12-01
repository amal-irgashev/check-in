import streamlit as st
from utils import make_authenticated_request
from datetime import datetime

# Custom CSS styling
st.markdown("""
<style>
.container {
    background-color: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    background-color: #f0f0f0;
    padding-left: 0.5rem;
}

.stButton>button {
    width: 100%;
    border-radius: 5px;
}

.stTextInput>div>div>input {
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

st.title("👤 Profile")

if not st.session_state.authenticated:
    st.warning("🔒 Please log in to view your profile")
else:
    user = st.session_state.user
    
    # Profile section
    st.markdown('<div class="container">', unsafe_allow_html=True)
    st.header("🪪 User Information")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### Personal Details")
        st.markdown(f"**📧 Email**  \n{user.email}")
        
    with col2:
        st.markdown("### Edit Profile")
        name = st.text_input("Full Name", 
                            value=user.user_metadata.get('full_name', ''),
                            placeholder="Enter your full name")
        
        if st.button("💾 Update Profile", type="primary"):
            try:
                make_authenticated_request(
                    "POST", 
                    "api/profile/update",
                    {
                        "full_name": name
                    }
                )
                st.success("✅ Profile updated successfully!")
            except Exception as e:
                st.error(f"❌ Update failed: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats section
    st.markdown('<div class="container">', unsafe_allow_html=True)
    st.header("📊 Statistics")
    
    try:
        stats = make_authenticated_request("GET", "api/profile/stats")
        
        cols = st.columns(3)
        with cols[0]:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("📝 Total Entries", stats.get('total_entries', 0))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with cols[1]:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("📅 Days Active", stats.get('days_active', 0))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with cols[2]:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.metric("📈 Entries/Week", f"{stats.get('avg_entries_per_week', 0):.1f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        member_since = datetime.fromisoformat(stats.get('member_since', '').replace('Z', '+00:00')).strftime('%B %d, %Y') if stats.get('member_since') else 'N/A'
        st.markdown(f"**🎉 Member Since:** {member_since}")
        
        if stats.get('recent_activity'):
            st.markdown("### 📋 Recent Activity")
            for activity in stats['recent_activity']:
                st.markdown(f'<div class="activity-item">• {activity}</div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error("❌ Unable to load statistics")
    
    st.markdown('</div>', unsafe_allow_html=True)