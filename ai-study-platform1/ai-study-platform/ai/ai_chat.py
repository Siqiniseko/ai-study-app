import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

SYSTEM_PROMPT = """You are StudyMind AI, an expert academic tutor and study assistant. 
You help students understand complex topics, answer questions clearly, and guide them 
through their learning journey. Be encouraging, precise, and educational. 
Use examples, analogies, and structured explanations. When appropriate, suggest 
related topics the student might want to explore."""

def get_chat_response(user_message: str, history: list) -> str:
    messages = []
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"
