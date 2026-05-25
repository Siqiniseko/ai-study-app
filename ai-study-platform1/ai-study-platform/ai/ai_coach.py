import anthropic
import os
from ai.local_generators import local_coaching_advice, local_study_plan

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

def generate_study_plan(goal: str, deadline: str, subjects: str, hours_per_day: int) -> str:
    if not os.environ.get('ANTHROPIC_API_KEY', '').strip():
        return local_study_plan(goal, deadline, subjects, hours_per_day)

    prompt = f"""Create a detailed, actionable study plan.

Goal: {goal}
Deadline: {deadline}
Subjects/Topics: {subjects}
Available study time: {hours_per_day} hours per day

Create a structured week-by-week study plan with:
- Daily schedule breakdown
- Specific topics to cover each day
- Study techniques for each subject
- Milestones and checkpoints
- Tips for staying on track

Format it clearly with sections and bullet points."""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return local_study_plan(goal, deadline, subjects, hours_per_day)

def get_coaching_advice(performance_data: list) -> str:
    if not os.environ.get('ANTHROPIC_API_KEY', '').strip():
        return local_coaching_advice(performance_data)

    if not performance_data:
        prompt = "Give general study advice and tips for a student just starting their learning journey."
    else:
        summary = "\n".join([f"- {d['topic']}: {d['score']}/{d['total']} ({round(d['score']/d['total']*100)}%)" 
                             for d in performance_data])
        prompt = f"""Analyze this student's quiz performance and give personalized coaching advice:

{summary}

Provide:
1. Strengths to celebrate
2. Areas needing improvement  
3. Specific study strategies for weak topics
4. Motivational encouragement
5. Next steps"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return local_coaching_advice(performance_data)
