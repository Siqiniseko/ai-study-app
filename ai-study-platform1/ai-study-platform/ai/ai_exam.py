import anthropic
import os
import json
import re

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

def create_exam(text: str, duration_minutes: int = 30) -> list:
    num_questions = max(5, duration_minutes // 3)
    prompt = f"""Create a {duration_minutes}-minute exam with {num_questions} questions based on this material.
Mix question types. Return ONLY a JSON array:
[
  {{
    "type": "mcq",
    "question": "Question text?",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
    "correct": 0,
    "marks": 2,
    "explanation": "Explanation"
  }},
  {{
    "type": "true_false",
    "question": "Statement to evaluate.",
    "correct": true,
    "marks": 1,
    "explanation": "Explanation"
  }}
]

Use mostly "mcq" and some "true_false" types.

Material:
{text[:3000]}"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw)
    except Exception as e:
        return []
