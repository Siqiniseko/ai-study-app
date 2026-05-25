import re
from collections import Counter

from ai.local_tutor import STOPWORDS, tokenize


def sentences_from_text(text: str) -> list[str]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text or "")
        if len(sentence.strip()) >= 35
    ]
    return sentences[:80]


def keywords_from_text(text: str, limit: int = 12) -> list[str]:
    counts = Counter(tokenize(text))
    return [word for word, _ in counts.most_common(limit)]


def local_summary(text: str) -> str:
    sentences = sentences_from_text(text)
    if not sentences:
        return "Not enough content to summarize. Add more study material first."

    keywords = keywords_from_text(text, 10)
    scored = []
    keyword_set = set(keywords)
    for sentence in sentences:
        score = len(keyword_set.intersection(tokenize(sentence)))
        scored.append((score, len(sentence), sentence))
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    key_sentences = [item[2] for item in scored[:5]]

    return (
        "**Key Concepts**\n"
        + "\n".join(f"- {word.title()}" for word in keywords[:6])
        + "\n\n**Important Details**\n"
        + "\n".join(f"- {sentence}" for sentence in key_sentences[:4])
        + "\n\n**Key Takeaways**\n"
        "- Review the repeated terms first.\n"
        "- Turn each important detail into one flashcard.\n"
        "- Test yourself without looking at the original notes."
    )


def local_flashcards(text: str, count: int = 10) -> list[dict]:
    sentences = sentences_from_text(text)
    keywords = keywords_from_text(text, count)
    cards = []

    for word in keywords:
        source = next((sentence for sentence in sentences if word in tokenize(sentence)), "")
        if source:
            cards.append({
                "front": f"What should you remember about {word}?",
                "back": source
            })
        if len(cards) >= count:
            break

    if not cards and text.strip():
        cards.append({
            "front": "What is the main idea of this material?",
            "back": text.strip()[:300]
        })

    return cards[:count]


def _option_pool(text: str, correct: str) -> list[str]:
    words = [word.title() for word in keywords_from_text(text, 18) if word.lower() != correct.lower()]
    fallback = ["Definition", "Example", "Process", "Result", "Evidence", "Comparison"]
    pool = []
    for word in words + fallback:
        if word not in pool:
            pool.append(word)
    return pool


def local_quiz(text: str, num_questions: int = 5) -> list[dict]:
    sentences = sentences_from_text(text)
    keywords = keywords_from_text(text, num_questions * 2)
    questions = []

    for word in keywords:
        source = next((sentence for sentence in sentences if word in tokenize(sentence)), "")
        if not source:
            continue
        options = [word.title()] + _option_pool(text, word)[:3]
        questions.append({
            "question": f"Which term best connects to this idea: {source[:180]}",
            "options": [f"{chr(65 + index)}) {option}" for index, option in enumerate(options)],
            "correct": 0,
            "explanation": f"The note connects this idea with {word}."
        })
        if len(questions) >= num_questions:
            break

    if not questions:
        questions.append({
            "question": "What should you do before generating a quiz?",
            "options": [
                "A) Add more study material",
                "B) Close the app",
                "C) Delete all notes",
                "D) Skip revision"
            ],
            "correct": 0,
            "explanation": "The quiz generator needs study material to build useful questions."
        })

    return questions


def local_exam(text: str, duration_minutes: int = 30) -> list[dict]:
    question_count = max(5, min(20, duration_minutes // 3))
    quiz_questions = local_quiz(text, question_count)
    exam = []
    for index, question in enumerate(quiz_questions):
        item = dict(question)
        item["type"] = "mcq"
        item["marks"] = 2
        exam.append(item)

        if index % 3 == 1 and len(exam) < question_count:
            sentence = sentences_from_text(text)[index % max(len(sentences_from_text(text)), 1)] if sentences_from_text(text) else "This material needs more detail."
            exam.append({
                "type": "true_false",
                "question": sentence[:220],
                "correct": True,
                "marks": 1,
                "explanation": "This statement is taken from the supplied study material."
            })

    return exam[:question_count]


def local_study_plan(goal: str, deadline: str, subjects: str, hours_per_day: int) -> str:
    topics = [topic.strip() for topic in re.split(r",|\n", subjects or "") if topic.strip()]
    if not topics:
        topics = ["core concepts", "practice questions", "revision notes"]

    daily_blocks = max(1, int(hours_per_day or 1))
    return (
        f"**Goal**\n{goal or 'Build a stronger study routine'}\n\n"
        f"**Deadline**\n{deadline or 'No deadline set'}\n\n"
        "**Weekly Structure**\n"
        "- Day 1: Review the first topic and write a one-page summary.\n"
        "- Day 2: Create flashcards for definitions, formulas, and examples.\n"
        "- Day 3: Practice questions without notes, then mark mistakes.\n"
        "- Day 4: Re-study weak areas and explain them out loud.\n"
        "- Day 5: Take a timed quiz or mock exam.\n"
        "- Day 6: Fix mistakes and update flashcards.\n"
        "- Day 7: Light review and plan the next week.\n\n"
        "**Topic Rotation**\n"
        + "\n".join(f"- {topic}: {daily_blocks} focused block(s) per study day" for topic in topics)
        + "\n\n**Checkpoints**\n"
        "- Track quiz scores after every practice session.\n"
        "- Revisit low-confidence flashcards every 24 to 48 hours.\n"
        "- If a topic scores under 70%, schedule it again before moving on."
    )


def local_coaching_advice(performance_data: list) -> str:
    if not performance_data:
        return (
            "**Start Here**\n"
            "- Add notes for one subject.\n"
            "- Generate a short quiz from those notes.\n"
            "- Review the questions you miss, then make flashcards.\n\n"
            "**Study Strategy**\n"
            "Use active recall first, then spaced repetition. Re-reading is useful only after you know what you got wrong."
        )

    weak = []
    strong = []
    for item in performance_data:
        total = item.get("total") or 1
        pct = round((item.get("score", 0) / total) * 100)
        row = f"{item.get('topic', 'Topic')}: {pct}%"
        if pct >= 70:
            strong.append(row)
        else:
            weak.append(row)

    return (
        "**Strengths**\n"
        + ("\n".join(f"- {item}" for item in strong) if strong else "- No strong areas yet. Keep collecting quiz data.")
        + "\n\n**Areas to Improve**\n"
        + ("\n".join(f"- {item}" for item in weak) if weak else "- No weak areas found in the current results.")
        + "\n\n**Next Steps**\n"
        "- Redo missed questions without looking at the answers.\n"
        "- Make one flashcard for each mistake.\n"
        "- Take another short quiz after a break and compare the score."
    )
