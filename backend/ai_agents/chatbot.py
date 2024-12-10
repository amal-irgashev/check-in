from typing import Dict, List, Generator
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from services.database_service import DatabaseService
from db.supabase_client import get_client
from services.chat_service import ChatService

# Setup 
load_dotenv()
logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



async def get_chat_response(user_id: str, message: str, window_id: str, conversation_history: List[Dict] = None) -> Generator:
    """Generates a streaming response from Levi, an AI chatbot that provides personalized insights."""
    try:
        # Get or initialize chat history
        conversation_history = conversation_history or await ChatService.get_chat_history(user_id, window_id)
        
        # Save user message and generate title if first message
        await ChatService.save_message(user_id, window_id, "user", message)
        if not conversation_history:
            await ChatService.generate_and_update_title(user_id, window_id, message)


        # Get user data and context
        supabase = get_client()
        user = supabase.auth.get_user()
        user_name = user.user.user_metadata.get('full_name', 'friend')
        
        # Get user stats
        entries = await DatabaseService.get_user_entries(user_id)
        total_entries = len(entries.data) if entries.data else 0
        
        first_entry = supabase.table("journal_entries")\
            .select("created_at")\
            .eq('user_id', user_id)\
            .order('created_at')\
            .limit(1)\
            .execute()
        member_since = first_entry.data[0]['created_at'] if first_entry.data else user.user.created_at


        # Get recent entries
        entries_result = DatabaseService.get_recent_entries(user_id, limit=5)
        entries_context = ""
        if not entries_result.error:
            entries_context = "\n".join([
                f"Entry Date: {entry.get('created_at', '')}\n"
                f"Content: {entry.get('entry', '')}\n"
                f"Analysis: Mood: {entry.get('journal_analyses', [{}])[0].get('mood', 'N/A')}, "
                f"Summary: {entry.get('journal_analyses', [{}])[0].get('summary', 'N/A')}, "
                f"Key Insights: {entry.get('journal_analyses', [{}])[0].get('key_insights', 'N/A')}\n"
                for entry in (entries_result.data or [])
            ])

        # Build context prompts
        system_prompt = f"""You are Levi, a friendly and empathetic AI companion. Your current conversation is with {user_name} (this is their actual name - always use it). 
        Maintain a warm, conversational tone while being professional. Your responses should be concise but meaningful. 
        Help {user_name} process their thoughts and feelings by referencing their journal entries, profile data, 
        and previous analyses. Keep responses concise and focus on being supportive and action driven. 
        When discussing patterns or progress, reference both journal entries and user statistics. Ask questions to help them reflect on their thoughts and feelings.""".strip()

        context_prompt = f"""User's Profile and Journal Context:

        Name: {user_name}
        Statistics:
        - Total Journal Entries: {total_entries}
        - Member Since: {member_since}

        Recent Journal Entries:
        {entries_context}

        Use this context to provide personalized responses. Reference specific entries, insights, or statistics 
        when relevant, but maintain a natural conversation flow. Always address {user_name} by name at least once in your response.""".strip()

        # Prepare messages for API
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{context_prompt}"},
            {"role": "system", "name": "system", "content": f"Remember: You are talking to {user_name}. Always use their name."}
        ]

        # Add conversation history and current message
        if conversation_history:
            for msg in conversation_history[-10:]:
                if msg["role"] == "user":
                    msg["name"] = user_name
                messages.append(msg)

        messages.append({"role": "user", "name": user_name, "content": message})

        # Get streaming response
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.2,
            messages=messages,
            max_tokens=3000,
            stream=True
        )

        # Stream response and save
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        
        await ChatService.save_message(user_id, window_id, "assistant", full_response)

    except Exception as e:
        logging.error(f"Error generating chat response: {str(e)}")
        error_message = "I apologize, but I encountered an error. Please try again."
        await ChatService.save_message(user_id, window_id, "assistant", error_message)
        yield error_message