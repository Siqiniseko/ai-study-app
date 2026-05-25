import json
import math
import os
import re
from collections import Counter
from datetime import datetime
from functools import lru_cache

from ai.training_corpus import TRAINING_CORPUS


STOPWORDS = {
    "about", "after", "again", "against", "also", "and", "are", "because",
    "been", "before", "being", "between", "both", "but", "can", "could",
    "did", "does", "doing", "down", "during", "each", "for", "from", "had",
    "has", "have", "having", "her", "here", "hers", "him", "his", "how",
    "into", "its", "just", "more", "most", "not", "now", "off", "once",
    "only", "other", "our", "out", "over", "same", "she", "should", "some",
    "such", "than", "that", "the", "their", "then", "there", "these", "they",
    "this", "those", "through", "too", "under", "until", "very", "was",
    "were", "what", "when", "where", "which", "while", "who", "why", "will",
    "with", "would", "you", "your"
}


def model_dir(base_path: str) -> str:
    path = os.path.join(base_path, "tutor_models")
    os.makedirs(path, exist_ok=True)
    return path


def model_path(base_path: str, user_id: int) -> str:
    return os.path.join(model_dir(base_path), f"user_{user_id}.json")


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9'-]{2,}", (text or "").lower())
        if token not in STOPWORDS
    ]


def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    parts = [part.strip() for part in re.split(r"\n{2,}|(?<=[.!?])\s+", text or "") if part.strip()]
    chunks = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + len(part) + 1 <= max_chars:
            current = f"{current} {part}"
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def build_documents(notes: list[dict], flashcards: list[dict], include_base: bool = True) -> list[dict]:
    documents = []
    if include_base:
        for item in TRAINING_CORPUS:
            documents.append({
                "source_type": "trained lesson",
                "source_title": item["title"],
                "subject": item["subject"],
                "chunk_index": 0,
                "text": item["text"],
            })

    for note in notes:
        title = note.get("title") or "Untitled note"
        text = "\n\n".join(
            part for part in [note.get("content") or "", note.get("summary") or ""] if part.strip()
        )
        for index, chunk in enumerate(chunk_text(text)):
            documents.append({
                "source_type": "note",
                "source_title": title,
                "chunk_index": index,
                "text": chunk,
            })

    for card in flashcards:
        deck = card.get("deck_name") or "Flashcards"
        front = card.get("front") or ""
        back = card.get("back") or ""
        text = f"Question: {front}\nAnswer: {back}".strip()
        if text:
            documents.append({
                "source_type": "flashcard",
                "source_title": deck,
                "chunk_index": 0,
                "text": text,
            })
    return documents


def build_model_from_documents(documents: list[dict], notes_count: int = 0, flashcards_count: int = 0) -> dict:
    tokenized = [tokenize(doc["text"]) for doc in documents]
    document_frequency = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    doc_count = max(len(documents), 1)
    idf = {
        token: round(math.log((doc_count + 1) / (freq + 1)) + 1, 6)
        for token, freq in document_frequency.items()
    }

    for doc, tokens in zip(documents, tokenized):
        counts = Counter(tokens)
        total = max(sum(counts.values()), 1)
        doc["vector"] = {
            token: round((count / total) * idf.get(token, 1.0), 6)
            for token, count in counts.items()
        }

    model = {
        "version": 1,
        "trained_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_counts": {
            "base_lessons": len(TRAINING_CORPUS),
            "notes": notes_count,
            "flashcards": flashcards_count,
            "chunks": len(documents),
        },
        "idf": idf,
        "documents": documents,
    }
    return model


@lru_cache(maxsize=1)
def base_tutor_model() -> dict:
    return build_model_from_documents(build_documents([], [], include_base=True))


def train_tutor_model(base_path: str, user_id: int, notes: list[dict], flashcards: list[dict]) -> dict:
    documents = build_documents(notes, flashcards, include_base=True)
    model = build_model_from_documents(documents, len(notes), len(flashcards))
    with open(model_path(base_path, user_id), "w", encoding="utf-8") as file:
        json.dump(model, file, ensure_ascii=True, indent=2)
    return model


def load_tutor_model(base_path: str, user_id: int) -> dict | None:
    path = model_path(base_path, user_id)
    if not os.path.exists(path):
        return base_tutor_model()
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def tutor_model_status(base_path: str, user_id: int) -> dict:
    path = model_path(base_path, user_id)
    if not os.path.exists(path):
        model = base_tutor_model()
        return {
            "trained": True,
            "user_trained": False,
            "trained_at": model.get("trained_at"),
            "source_counts": model.get("source_counts", {}),
        }
    model = load_tutor_model(base_path, user_id)
    return {
        "trained": True,
        "user_trained": True,
        "trained_at": model.get("trained_at"),
        "source_counts": model.get("source_counts", {}),
    }


def retrieve_context(model: dict | None, query: str, limit: int = 4) -> list[dict]:
    if not model:
        return []

    query_counts = Counter(tokenize(query))
    if not query_counts:
        return []
    query_terms = set(query_counts)

    idf = model.get("idf", {})
    total = max(sum(query_counts.values()), 1)
    query_vector = {
        token: (count / total) * idf.get(token, 1.0)
        for token, count in query_counts.items()
    }
    query_norm = math.sqrt(sum(weight * weight for weight in query_vector.values())) or 1.0

    scored = []
    for doc in model.get("documents", []):
        vector = doc.get("vector", {})
        if not vector:
            continue
        dot = sum(query_vector.get(token, 0.0) * vector.get(token, 0.0) for token in query_vector)
        if dot <= 0:
            continue
        doc_norm = math.sqrt(sum(weight * weight for weight in vector.values())) or 1.0
        score = dot / (query_norm * doc_norm)
        title_terms = set(tokenize(doc.get("source_title", "")))
        subject_terms = set(tokenize(doc.get("subject", "")))
        score += 0.35 * len(query_terms.intersection(title_terms))
        score += 0.08 * len(query_terms.intersection(subject_terms))
        scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, doc in scored[:limit]:
        item = dict(doc)
        item["score"] = round(score, 4)
        item.pop("vector", None)
        results.append(item)
    return results


def _best_sentences(query: str, documents: list[dict], max_sentences: int = 4) -> list[str]:
    query_terms = set(tokenize(query))
    candidates = []
    for doc in documents:
        for sentence in re.split(r"(?<=[.!?])\s+", doc.get("text", "")):
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            overlap = len(query_terms.intersection(tokenize(sentence)))
            candidates.append((overlap, len(sentence), sentence))
    candidates.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    picked = []
    seen = set()
    for overlap, _, sentence in candidates:
        key = sentence.lower()
        if overlap == 0 or key in seen:
            continue
        picked.append(sentence)
        seen.add(key)
        if len(picked) == max_sentences:
            break
    return picked


def generate_local_response(user_message: str, history: list | None, model: dict | None) -> str:
    context = retrieve_context(model, user_message, limit=4)
    if not context:
        return (
            "I can help, but I do not have trained study material for this question yet.\n\n"
            "**Best next step**\n"
            "Add notes or flashcards, then press **Train tutor**. After that I can answer using your own material.\n\n"
            "**For now**\n"
            "- Tell me the topic you are studying.\n"
            "- Paste a short paragraph or problem.\n"
            "- Ask for an explanation, examples, a quiz, or a step-by-step walkthrough."
        )

    sources = []
    for doc in context:
        label = f"{doc.get('source_title', 'Study material')} ({doc.get('source_type', 'source')})"
        if label not in sources:
            sources.append(label)

    key_points = _best_sentences(user_message, context)
    if not key_points:
        key_points = [doc.get("text", "")[:220].strip() for doc in context if doc.get("text")]
    primary_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", context[0].get("text", ""))
        if sentence.strip()
    ]
    short_answer = primary_sentences[0] if primary_sentences else context[0].get("text", "")[:280]
    for sentence in primary_sentences:
        if set(tokenize(user_message)).intersection(tokenize(sentence)):
            short_answer = sentence
            break
    merged_points = []
    for sentence in [short_answer] + key_points:
        if sentence and sentence not in merged_points:
            merged_points.append(sentence)
    key_points = merged_points[:4]

    bullets = "\n".join(f"- {point[:300]}" for point in key_points[:4])
    source_text = ", ".join(sources[:3])
    study_check = key_points[0][:180] if key_points else "Explain the concept in your own words."

    return (
        f"I found the strongest match in my trained tutor model: {source_text}.\n\n"
        "**Short Answer**\n"
        f"{short_answer}\n\n"
        "**Key Points**\n"
        f"{bullets}\n\n"
        "**Tutor Check**\n"
        f"Try explaining this back in one sentence: {study_check}\n\n"
        "**Study Move**\n"
        "Make one flashcard for the main definition and one for an example, then test yourself without looking."
    )
