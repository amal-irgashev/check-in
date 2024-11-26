# AI assistant that helps users reflect on their journal entries and provides supportive observations

from typing import Dict, List
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import logging
from db.models import journal_entry, journal_analysis
from supabase import create_client, Client

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def analyze_journal_patterns(user_id: str, query: str = None) -> Dict:
    """
    Analyzes patterns across multiple journal entries and answers questions using OpenAI's GPT model.
    Acts as a supportive observer to help users reflect on their journaling.
    
    Args:
        user_id: ID of the user whose entries to analyze
        query: Optional specific question from user about their journaling patterns
    
    Returns:
        Dict containing the analysis response
    """
    try:
        # Fetch entries from Supabase
        entries_result = supabase.table("journal_entries")\
            .select("*, journal_analyses(*)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
            
        if not entries_result.data:
            return {"response": "I don't see any journal entries yet. Would you like to share what's on your mind? I'm here to listen and help you reflect on your thoughts."}
            
        # Format entries for context
        entries_context = []
        for entry in entries_result.data:
            analysis = entry["journal_analyses"][0] if entry["journal_analyses"] else {}
            entry_text = f"""
Entry: {entry["entry"]}
Date: {entry["created_at"]}
Mood: {analysis.get("mood", "unknown")}
Categories: {analysis.get("categories", [])}
"""
            entries_context.append(entry_text)

        entries_text = "\n---\n".join(entries_context)

        # System message defines the AI's role
        system_message = """You are a supportive assistant helping users reflect on their journal entries.
Your approach should be:
- Warm and empathetic
- Conversational and concise
- Focused on helping users gain their own insights
- Observant of patterns and themes
- Encouraging of self-reflection
- Supportive without giving clinical advice
- Focused on personal growth and self-awareness

When reviewing journal entries:
- Notice recurring themes and patterns
- Point out positive moments and growth
- Ask thoughtful questions to promote reflection
- Offer gentle observations
- Maintain appropriate boundaries by not providing medical/clinical advice"""

        # User message combines entries with any specific query
        user_message = f"""Here are the user's journal entries for context:

{entries_text}

Please help reflect on these entries by:
1. Noting any recurring themes or patterns
2. Highlighting moments of insight or growth
3. Making gentle observations that might help with self-reflection
4. Asking thoughtful questions to deepen understanding

"""
        if query:
            user_message += f"\nUser's Question/Concern: {query}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=4000,
        )

        return {"response": response.choices[0].message.content}

    except Exception as e:
        logging.error(f"Pattern analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze journal patterns")

def get_chat_response(user_id: str, message: str) -> str:
    """
    Provides supportive responses and journal analysis as a helpful observer.
    
    Args:
        user_id: ID of the user
        message: User's message/question
        
    Returns:
        String containing the AI's supportive response
    """
    try:
        # Check if message is about journal entries
        journal_keywords = ["journal", "entry", "entries", "wrote", "written", "diary"]
        is_journal_query = any(keyword in message.lower() for keyword in journal_keywords)
        
        if is_journal_query:
            # Analyze journal entries for the query
            response = analyze_journal_patterns(user_id, message)
        else:
            # Provide general supportive response
            system_message = """You are a supportive assistant helping users reflect on their thoughts and experiences. 
Respond with empathy and encouragement while helping users develop their own insights."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            response = {"response": response.choices[0].message.content}
            
        return response["response"]
        
    except Exception as e:
        logging.error(f"Chat response failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate chat response")
