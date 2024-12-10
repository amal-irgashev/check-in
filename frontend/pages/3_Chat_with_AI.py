import streamlit as st
from auth import init_auth
from utils import make_authenticated_request
import os
import json

# Initialize session state for chat windows
if "current_window_id" not in st.session_state:
    st.session_state.current_window_id = None
if "chat_windows" not in st.session_state:
    st.session_state.chat_windows = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "delete_confirmation" not in st.session_state:
    st.session_state.delete_confirmation = {}

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

# Sidebar for chat windows
with st.sidebar:
    st.title("Chat History")
    
    # New Chat button
    if st.button("New Chat"):
        response = make_authenticated_request("POST", "chat/window/create")
        if response and isinstance(response, dict) and "id" in response:
            st.session_state.current_window_id = response["id"]
            st.session_state.messages = []
            st.rerun()
    
    # List of existing chats
    try:
        windows_response = make_authenticated_request("GET", "chat/windows")
        if isinstance(windows_response, list):
            st.session_state.chat_windows = windows_response
            
            for window in st.session_state.chat_windows:
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    # Chat window button
                    if st.button(
                        window.get("title", "New Chat"),
                        key=f"window_{window['id']}", 
                        use_container_width=True
                    ):
                        st.session_state.current_window_id = window["id"]
                        history_response = make_authenticated_request(
                            "GET", 
                            f"chat/history/{window['id']}"
                        )
                        if isinstance(history_response, list):
                            st.session_state.messages = history_response
                        st.rerun()
                
                with col2:
                    # Rename button
                    if st.button("✏️", key=f"rename_{window['id']}", help="Rename chat"):
                        new_title = st.text_input(
                            "New title",
                            value=window.get("title", ""),
                            key=f"new_title_{window['id']}"
                        )
                        if st.button("Save", key=f"save_rename_{window['id']}"):
                            response = make_authenticated_request(
                                "PUT",
                                f"chat/window/{window['id']}/rename",
                                {"title": new_title}
                            )
                            if response:
                                st.rerun()
                
                with col3:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{window['id']}", help="Delete chat"):
                        st.session_state.delete_confirmation[window['id']] = True
                        st.rerun()
                    
                    if st.session_state.delete_confirmation.get(window['id']):
                        st.write("Are you sure?")
                        col3a, col3b = st.columns(2)
                        with col3a:
                            if st.button("Yes", key=f"confirm_delete_{window['id']}"):
                                response = make_authenticated_request(
                                    "DELETE",
                                    f"chat/window/{window['id']}"
                                )
                                if response:
                                    if st.session_state.current_window_id == window['id']:
                                        st.session_state.current_window_id = None
                                        st.session_state.messages = []
                                    st.session_state.delete_confirmation.pop(window['id'])
                                    st.rerun()
                        with col3b:
                            if st.button("No", key=f"cancel_delete_{window['id']}"):
                                st.session_state.delete_confirmation.pop(window['id'])
                                st.rerun()
    except Exception as e:
        st.error(f"Failed to load chat windows: {str(e)}")

# Main chat area
if st.session_state.current_window_id:
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
                    {
                        "message": prompt,
                        "window_id": st.session_state.current_window_id
                    },
                    stream=True
                )
                
                if response:
                    for chunk in response.iter_lines():
                        if chunk:
                            try:
                                chunk_text = chunk.decode()
                                if chunk_text.startswith('data: '):
                                    chunk_text = chunk_text[6:]
                                chunk_data = json.loads(chunk_text)
                                
                                if 'error' in chunk_data:
                                    st.error(chunk_data['error'])
                                    break
                                    
                                token = chunk_data.get('token', '')
                                full_response += token
                                message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                continue
                    
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_response
                    })
                else:
                    st.error("Failed to get response from AI")
        except Exception as e:
            if "User not authenticated" in str(e):
                st.error("Please log in to chat with AI")
            else:
                st.error(f"Error communicating with AI: {str(e)}")
else:
    st.info("Select a chat from the sidebar or start a new one")
