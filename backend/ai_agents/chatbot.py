from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from services.database_service import DatabaseService
from db.supabase_client import get_client
import openai
from typing import Generator


# client + logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_chat_response(user_id: str, message: str, conversation_history: List[Dict] = None) -> Generator:
    """
    Generates a streaming response from Levi, a friendly AI chatbot that provides personalized insights
    based on the user's journal entries, profile data, and conversation history.
    """
    try:
        # Get user's recent journal entries and analyses
        entries_result = DatabaseService.get_recent_entries(user_id, limit=5)
        
        # Get user directly from Supabase auth
        try:
            supabase = get_client()
            user_response = supabase.auth.get_user()
            user_name = user_response.user.user_metadata.get('full_name', 'friend')
            if not user_name:
                logging.warning(f"No name found for user {user_id}, defaulting to 'friend'")
                user_name = 'friend'
            
            # Get profile stats from journal entries
            entries_count = await DatabaseService.get_user_entries(user_id)
            total_entries = len(entries_count.data) if entries_count.data else 0
            
            # Get first entry date for member_since
            first_entry = supabase.table("journal_entries")\
                .select("created_at")\
                .eq('user_id', user_id)\
                .order('created_at')\
                .limit(1)\
                .execute()
                
            member_since = first_entry.data[0]['created_at'] if first_entry.data else user_response.user.created_at
            
            profile_context = f"""User Information:
            Name: {user_name}
            Statistics:
            - Total Journal Entries: {total_entries}
            - Member Since: {member_since}
            """
        except Exception as e:
            logging.error(f"Error getting user data: {str(e)}")
            profile_context = ""
            user_name = "friend"
            
        if entries_result.error:
            logging.error(f"Database error: {entries_result.error}")
            entries_context = ""
        else:
            entries_context = "\n".join([
                f"Entry Date: {entry.get('created_at', '')}\n"
                f"Content: {entry.get('entry', '')}\n"
                f"Analysis: Mood: {entry.get('journal_analyses', [{}])[0].get('mood', 'N/A')}, "
                f"Summary: {entry.get('journal_analyses', [{}])[0].get('summary', 'N/A')}, "
                f"Key Insights: {entry.get('journal_analyses', [{}])[0].get('key_insights', 'N/A')}\n"
                for entry in (entries_result.data or [])
            ])

        system_prompt = f"""You are Levi, a friendly and empathetic AI companion. Your current conversation is with {user_name} (this is their actual name - always use it). 
        Maintain a warm, conversational tone while being professional. Your responses should be concise but meaningful. 
        Help {user_name} process their thoughts and feelings by referencing their journal entries, profile data, 
        and previous analyses. Keep responses under 150 words and focus on being supportive and actionable. 
        When discussing patterns or progress, reference both journal entries and user statistics.""".strip()

        context_prompt = f"""User's Profile and Journal Context:

        {profile_context.strip()}

        Recent Journal Entries:
        {entries_context.strip()}

        Use this context to provide personalized responses. Reference specific entries, insights, or statistics 
        when relevant, but maintain a natural conversation flow. Always address {user_name} by name at least once in your response.""".strip()

        # Initialize messages list with combined system prompt
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{context_prompt}"},
            {"role": "system", "name": "system", "content": f"Remember: You are talking to {user_name}. Always use their name."}
        ]

        # Add conversation history with names
        if conversation_history:
            for msg in conversation_history[-10:]:
                if msg["role"] == "user":
                    msg["name"] = user_name
                messages.append(msg)

        # Add current user message with name
        messages.append({
            "role": "user", 
            "name": user_name,
            "content": message
        })

        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0.2,
            messages=messages,
            max_tokens=300,
            stream=True  
        )

        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logging.error(f"Error generating chat response: {str(e)}")
        if "model not found" in str(e).lower():
            yield "I apologize, but there seems to be an issue with the AI model configuration. Please contact support."
        else:
            yield f"I apologize, but I encountered an error: {str(e)}"