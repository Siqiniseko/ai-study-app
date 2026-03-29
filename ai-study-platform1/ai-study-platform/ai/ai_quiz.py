import anthropic
import os
import json
import re

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

def create_quiz(text: str, num_questions: int = 5) -> list:
    prompt = f"""Create {num_questions} multiple choice quiz questions based on this study material.
Return ONLY a JSON array with no markdown, no explanation. Format:
[
  {{
    "question": "Question text here?",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct": 0,
    "explanation": "Why this answer is correct"
  }}
]
correct is the 0-based index of the correct option.

Study material:
{text[:3000]}"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception as e:
        return [{"question": "Quiz generation failed. Please try again.", 
                 "options": ["A) Error", "B) Error", "C) Error", "D) Error"],
                 "correct": 0, "explanation": str(e)}]
