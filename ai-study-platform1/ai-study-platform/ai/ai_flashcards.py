import anthropic
import os
import json
import re

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

def create_flashcards(text: str, count: int = 10) -> list:
    prompt = f"""Create {count} study flashcards from this content.
Return ONLY a JSON array with no markdown:
[
  {{"front": "Question or term on front of card", "back": "Answer or definition on back"}}
]

Make fronts concise questions or key terms. Make backs clear, complete answers.

Content:
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
        return [{"front": "Error generating flashcards", "back": str(e)}]
