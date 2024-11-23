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
    Analyzes a journal entry using OpenAI to extract mood and summary.
    Returns a dictionary with mood and a brief summary.
    """
    prompt = """Analyze this journal entry and provide:
1. mood: The primary mood/emotion expressed (choose exactly one):
   - joyful
   - content 
   - neutral
   - anxious
   - sad
   - angry
   - frustrated
   - excited
   - grateful
   - overwhelmed

2. summary: A brief personal reflection capturing the core feeling and main event/thought (1 sentence)

Respond with a JSON object containing 'mood' and 'summary' keys."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are an expert journal analyst. Respond with clean JSON only."},
                {"role": "user", "content": f"{prompt}\n\nJournal entry:\n{text}"}
            ]
        )
        #parse response
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace('```json', '').replace('```', '')
        
        analysis = json.loads(response_text)
        
        if 'mood' not in analysis or 'summary' not in analysis:
            raise ValueError("Response missing required fields")
            
        return analysis
        
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON response: {response_text}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        logging.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze journal entry")
