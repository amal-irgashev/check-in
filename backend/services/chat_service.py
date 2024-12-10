from typing import List, Dict, Optional
from db.supabase_client import get_client
from datetime import datetime, timedelta
import logging
import os
from openai import OpenAI

class ChatService:
    @staticmethod
    async def create_chat_window(user_id: str, title: str = "New Chat") -> Dict:
        """Create a new chat window"""
        try:
            supabase = get_client()
            result = supabase.table('chat_windows').insert({
                "user_id": user_id,
                "title": title
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating chat window: {str(e)}")
            return None

    @staticmethod
    async def get_chat_windows(user_id: str) -> List[Dict]:
        """Get all chat windows for a user"""
        try:
            supabase = get_client()
            result = supabase.table('chat_windows')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('last_updated', desc=True)\
                .execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting chat windows: {str(e)}")
            return []

    @staticmethod
    async def get_chat_history(user_id: str, window_id: str) -> List[Dict]:
        """Get chat history for a specific window"""
        try:
            supabase = get_client()
            result = supabase.table('chat_history')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('window_id', window_id)\
                .order('created_at')\
                .execute()
            
            return [
                {"role": msg["role"], "content": msg["content"]}
                for msg in (result.data or [])
            ]
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []

    @staticmethod
    async def save_message(user_id: str, window_id: str, role: str, content: str) -> None:
        """Save a chat message to the database"""
        try:
            supabase = get_client()
            # Save message
            supabase.table('chat_history').insert({
                "user_id": user_id,
                "window_id": window_id,
                "role": role,
                "content": content
            }).execute()
            
            # Update window last_updated
            supabase.table('chat_windows')\
                .update({"last_updated": datetime.utcnow().isoformat()})\
                .eq('id', window_id)\
                .execute()
        except Exception as e:
            print(f"Error saving chat message: {str(e)}")

    @staticmethod
    async def update_window_title(window_id: str, title: str) -> None:
        """Update chat window title"""
        try:
            supabase = get_client()
            supabase.table('chat_windows')\
                .update({"title": title})\
                .eq('id', window_id)\
                .execute()
        except Exception as e:
            print(f"Error updating window title: {str(e)}")

    @staticmethod
    async def generate_and_update_title(user_id: str, window_id: str, message: str) -> None:
        """Generate and update chat window title based on first message"""
        try:
            # Check if this is the first message in the window
            supabase = get_client()
            history = supabase.table('chat_history')\
                .select('*')\
                .eq('window_id', window_id)\
                .execute()
            
            if len(history.data) <= 2:  # Only user message and AI response
                # Generate title using OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Generate a very short, concise title (4-6 words max) for a chat conversation that starts with this message. Make it descriptive but brief."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    max_tokens=20,
                    temperature=0.3
                )
                
                title = response.choices[0].message.content.strip('" ')
                
                # Update window title
                supabase.table('chat_windows')\
                    .update({"title": title})\
                    .eq('id', window_id)\
                    .execute()
                    
        except Exception as e:
            logging.error(f"Error generating chat title: {str(e)}")

    @staticmethod
    async def delete_window(user_id: str, window_id: str) -> bool:
        """Delete a chat window and its messages"""
        try:
            supabase = get_client()
            # Delete all messages first
            supabase.table('chat_history')\
                .delete()\
                .eq('window_id', window_id)\
                .eq('user_id', user_id)\
                .execute()
            
            # Then delete the window
            result = supabase.table('chat_windows')\
                .delete()\
                .eq('id', window_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logging.error(f"Error deleting chat window: {str(e)}")
            return False

    @staticmethod
    async def rename_window(user_id: str, window_id: str, new_title: str) -> bool:
        """Rename a chat window"""
        try:
            supabase = get_client()
            result = supabase.table('chat_windows')\
                .update({"title": new_title})\
                .eq('id', window_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logging.error(f"Error renaming chat window: {str(e)}")
            return False