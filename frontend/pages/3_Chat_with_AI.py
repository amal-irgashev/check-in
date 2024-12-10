import streamlit as st
from auth import init_auth
from utils import make_authenticated_request
import os
import json

# Get the directory where the current script is located
current_dir = os.path.dirname(__file__)
# Construct path to assets relative to current script
image_path = os.path.join(current_dir, "..", "assets", "levi_avatar.png")

st.set_page_config(page_icon=image_path)

init_auth()

if not st.session_state.authenticated:
    st.warning("Please login to access this feature.")
    st.stop()

st.title("💬 Chat with Levi")



# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    avatar = image_path if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
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
        with st.chat_message("assistant", avatar=image_path):
            message_placeholder = st.empty()
            full_response = ""
            
            # Make streaming request
            response = make_authenticated_request(
                "POST",
                "chat",
                {"message": prompt},
                stream=True  # Enable streaming in the request
            )
            
            if response:
                for chunk in response.iter_lines():
                    if chunk:
                        try:
                            # Remove 'data: ' prefix from SSE format
                            chunk_text = chunk.decode()
                            if chunk_text.startswith('data: '):
                                chunk_text = chunk_text[6:]
                            chunk_data = json.loads(chunk_text)
                            
                            if 'error' in chunk_data:
                                st.error(chunk_data['error'])
                                break
                                
                            token = chunk_data.get('token', '')
                            full_response += token
                            # Update placeholder with accumulated tokens
                            message_placeholder.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            continue  # Skip invalid JSON chunks
                
                # Update placeholder one final time without cursor
                message_placeholder.markdown(full_response)
                # Add AI response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error("Failed to get response from AI")
    except Exception as e:
        if "User not authenticated" in str(e):
            st.error("Please log in to chat with AI")
        else:
            st.error(f"Error communicating with AI: {str(e)}")
