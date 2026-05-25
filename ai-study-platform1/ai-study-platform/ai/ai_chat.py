import os

import anthropic

from ai.local_tutor import generate_local_response, retrieve_context


SYSTEM_PROMPT = """You are StudyMind AI, an expert academic tutor and study assistant.
You help students understand complex topics, answer questions clearly, and guide them
through their learning journey. Be encouraging, precise, and educational.
Use examples, step-by-step reasoning, and structured explanations. When trained
study context is provided, prioritize that context and cite the source titles."""


def _anthropic_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _build_context_block(tutor_model: dict | None, user_message: str) -> str:
    matches = retrieve_context(tutor_model, user_message, limit=4)
    if not matches:
        return ""

    sections = []
    for index, match in enumerate(matches, start=1):
        title = match.get("source_title", "Study material")
        source_type = match.get("source_type", "source")
        text = match.get("text", "")
        sections.append(f"[{index}] {title} ({source_type})\n{text[:1200]}")
    return "\n\n".join(sections)


def get_chat_response(user_message: str, history: list, tutor_model: dict | None = None) -> str:
    context_block = _build_context_block(tutor_model, user_message)
    client = _anthropic_client()

    if client:
        messages = []
        for item in history[-12:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

        if context_block:
            user_content = (
                "Use this trained study context if relevant. If it does not answer the question, say so clearly.\n\n"
                f"{context_block}\n\n"
                f"Student question: {user_message}"
            )
        else:
            user_content = user_message
        messages.append({"role": "user", "content": user_content})

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1200,
                system=SYSTEM_PROMPT,
                messages=messages
            )
            return response.content[0].text
        except Exception:
            pass

    return generate_local_response(user_message, history, tutor_model)
