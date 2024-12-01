from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from services.database_service import DatabaseService
import openai

# Configure logging and OpenAI client
load_dotenv()
logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_chat_response(user_id: str, message: str, conversation_history: List[Dict] = None) -> str:
    """
    Generates a response from Levi, a friendly AI chatbot that provides personalized insights
    based on the user's journal entries and conversation history.
    """
    try:
        # Get user's recent journal entries and analyses
        entries_result = DatabaseService.get_recent_entries(user_id, limit=3)
        
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

        system_prompt = """You are Levi, a friendly and empathetic AI companion. You speak in a warm, 
        conversational tone while maintaining professionalism. Your responses are concise but meaningful. 
        You help users process their thoughts and feelings by referencing their journal entries and previous 
        analyses. Keep responses under 150 words and focus on being supportive and actionable. When discussing 
        journal entries, refer to specific insights and patterns you notice."""

        context_prompt = f"""User's recent journal context:\n{entries_context}\n
        Use this context to provide personalized responses. Reference specific entries or insights when relevant, 
        but maintain a natural conversation flow. If no journal entries are available, focus on being a supportive 
        conversation partner."""

        # Initialize messages list with system prompts
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_prompt}
        ]

        # Add conversation history if provided
        if conversation_history:
            # Only include last 5 messages to maintain context without overloading
            messages.extend(conversation_history[-5:])

        # Add current user message
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using standard GPT-4 model
            temperature=0.4,  # Slightly higher temperature for more dynamic responses
            messages=messages,
            max_tokens=200  # Ensure concise responses
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating chat response: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."