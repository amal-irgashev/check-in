# functionlaity:
# - analyze journal entry (mood, summary, categories, key insights)
# - return analysis as json
# - maybe add te ability to 



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
    Analyzes a journal entry using OpenAI's GPT model acting as an expert psychologist to extract 
    meaningful psychological insights and patterns. Returns a structured analysis focusing on emotional 
    state, key themes, and actionable insights for personal growth.
    """
    prompt = """As an expert psychologist, analyze this journal entry with empathy and psychological insight. 
Provide a structured analysis in the following format:

1. mood: Identify the primary emotional state (select exactly one):
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

2. summary: Write one clear, empathetic sentence that captures both the main experience/thought 
   and its emotional impact on the writer

3. categories: Identify the key life domains discussed (select all that apply):
   - health (physical and mental well-being)
   - career (work and professional development)
   - relationships (social connections and interactions)
   - personal_growth (learning and self-development)
   - daily_life (routine activities and general experiences)

4. key_insights: Provide one psychologically-informed, actionable insight that the writer can 
   use for self-reflection or positive change

Format your response as a JSON object with keys: 'mood', 'summary', 'categories', and 'key_insights'.
Focus on providing clear, empathetic, and professionally-grounded psychological insights."""

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
