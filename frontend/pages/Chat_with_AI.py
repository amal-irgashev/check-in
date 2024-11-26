import streamlit as st
from auth import init_auth
from utils import make_authenticated_request

init_auth()

if not st.session_state.authenticated:
    st.warning("Please login to access this feature.")
    st.stop()

st.title("Chat with Your Journal AI")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your journal entries..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = make_authenticated_request(
                    "POST",
                    "chat",
                    {"message": prompt}
                )
                if response:
                    ai_response = response["response"]
                    st.markdown(ai_response)
                    # Add AI response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("Failed to get response from AI")
    except Exception as e:
        if "User not authenticated" in str(e):
            st.error("Please log in to chat with AI")
        else:
            st.error(f"Error communicating with AI: {str(e)}")
