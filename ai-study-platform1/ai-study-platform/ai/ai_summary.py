import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

def generate_summary(text: str) -> str:
    if not text or len(text.strip()) < 50:
        return "Not enough content to summarize."
    
    prompt = f"""Summarize the following study material clearly and concisely. 
Structure your summary with:
- **Key Concepts**: Main ideas (bullet points)
- **Important Details**: Supporting facts
- **Key Takeaways**: What to remember

Text to summarize:
{text[:4000]}"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Summary generation failed: {str(e)}"
