import streamlit as st
from auth import init_auth
from utils import make_authenticated_request

# Page settings - must be first Streamlit command
st.set_page_config(
    page_title="📝 Smart Journal",
    page_icon="📔",
    layout="wide"
)

# Initialize authentication
init_auth()

# CSS styling
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

# Hide sidebar navigation when not authenticated
if not st.session_state.get('authenticated', False):
    # Hide sidebar with CSS
    st.markdown("""
        <style>
        [data-testid="collapsedControl"] {display: none;}
        </style>
        """, unsafe_allow_html=True)

# Show authentication page if not authenticated
if not st.session_state.authenticated:
    st.title("Welcome to Smart Journal")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            # login user
            if login_submitted:
                from auth import sign_in
                if sign_in(login_email, login_password):
                    st.success("Successfully logged in!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

    with tab2:
        with st.form("signup_form"):
            signup_email = st.text_input("Email")
            signup_password = st.text_input("Password", type="password")
            signup_password_confirm = st.text_input("Confirm Password", type="password")
            signup_submitted = st.form_submit_button("Sign Up")
            
            if signup_submitted:
                if signup_password != signup_password_confirm:
                    st.error("Passwords do not match!")
                else:
                    from auth import signup_user
                    if signup_user(signup_email, signup_password):
                        st.info("Please go to the Login tab to sign in.")
else:
    # Add logout button in top right
    col1, col2 = st.columns([6,1])
    with col1:
        st.title("📝 Smart Journal")
    with col2:
        from auth import logout_user
        if st.button("Logout"):
            logout_user()
            st.rerun()
    
    # Get user stats including name
    try:
        stats = make_authenticated_request("GET", "api/profile/stats")
        name = stats.get('full_name') or st.session_state.user.email
        st.write(f"Welcome back, {name}!")
    except Exception as e:
        st.write(f"Welcome back, {st.session_state.user.email}!")
        
    st.write("Please use the navigation menu on the left to access different features.")