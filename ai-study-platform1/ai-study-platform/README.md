# StudyMind AI — AI-Powered Study Platform

A full-featured study platform built with Flask and Claude AI, featuring notes, flashcards, quizzes, mock exams, a study planner, AI coaching, and analytics.

## Features

- **AI Tutor Chat** — Conversational tutor powered by Claude
- **Smart Notes** — Create, edit, and auto-summarise notes
- **PDF/Image Upload** — OCR text extraction from uploaded files
- **Flashcards** — AI-generated decks with spaced repetition confidence tracking
- **Quizzes** — Generate multiple-choice quizzes from any text
- **Mock Exams** — Timed exams with mixed question types
- **Study Planner** — AI-generated personalised study schedules
- **AI Coach** — Performance analysis and study advice
- **Analytics** — Charts tracking quiz scores and progress
- **Admin Panel** — User management (admin role)

## Setup

### 1. Clone & install dependencies

```bash
cd ai-study-platform
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. (Optional) Install Tesseract OCR for image/scanned PDF support

```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows — download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Run the app

```bash
python app.py
```

Visit `http://localhost:5000` and register your first account.

### 5. Create an admin account

After registering, open a Python shell:

```python
from app import app, db, User, bcrypt
with app.app_context():
    user = User.query.filter_by(email='your@email.com').first()
    user.role = 'admin'
    db.session.commit()
```

## Project Structure

```
ai-study-platform/
├── app.py              # Flask app, routes, models
├── config.py           # Configuration
├── requirements.txt
├── .env.example        # Copy to .env and fill in secrets
├── ai/
│   ├── ai_chat.py      # Conversational AI tutor
│   ├── ai_summary.py   # Note summarisation
│   ├── ai_quiz.py      # Quiz generation
│   ├── ai_flashcards.py # Flashcard generation
│   ├── ai_exam.py      # Exam generation
│   ├── ai_coach.py     # Coaching advice & study plans
│   └── ocr_reader.py   # PDF & image text extraction
├── static/
│   ├── css/main.css    # Full stylesheet
│   └── js/main.js      # Frontend logic
├── templates/          # Jinja2 HTML templates
├── database/db.sql     # Schema reference
└── uploads/notes_pdfs/ # Uploaded files (auto-created)
```

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Bcrypt
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **OCR**: PyMuPDF + Tesseract
- **Frontend**: Vanilla JS, Chart.js, custom CSS (dark academic theme)
- **Database**: SQLite (easily swappable to PostgreSQL)
