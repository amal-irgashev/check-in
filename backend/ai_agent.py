from typing import Dict
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import logging

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_journal_entry(text: str) -> Dict:
    """
    Analyzes a journal entry using OpenAI to extract insights including mood, summary,
    and categorization. Returns a dictionary with the analysis results.
    """
    prompt = """Analyze this journal entry and provide the following insights in a clear, concise format:

1. mood: The primary emotional state (select exactly one):
   - joyful (feeling happy and cheerful)
   - content (satisfied and at peace)
   - neutral (neither positive nor negative)
   - anxious (worried or uneasy)
   - sad (unhappy or down)
   - angry (feeling strong displeasure)
   - frustrated (annoyed or discouraged)
   - excited (enthusiastic and eager)
   - grateful (appreciative and thankful)
   - overwhelmed (feeling excessive pressure)

2. summary: One clear sentence capturing the main event/thought and associated feeling

3. categories: Primary life areas discussed (select all that apply):
   - health
   - career
   - relationships
   - personal_growth
   - daily_life

4. key_insights: One actionable insight or pattern identified from the entry

Respond with a JSON object containing 'mood', 'summary', 'categories', and 'key_insights' keys."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are an expert journal analyst focused on extracting clear, actionable insights. Respond with clean JSON only."},
                {"role": "user", "content": f"{prompt}\n\nJournal entry:\n{text}"}
            ]
        )
        
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace('```json', '').replace('```', '')
        
        analysis = json.loads(response_text)
        
        required_fields = ['mood', 'summary', 'categories', 'key_insights']
        if not all(field in analysis for field in required_fields):
            raise ValueError("Response missing required fields")
            
        return analysis
        
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON response: {response_text}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze journal entry")
