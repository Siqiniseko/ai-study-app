from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from config import Config
from datetime import datetime
import os, json

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FLASHCARD_FOLDER'], exist_ok=True)

# ─── Models ───────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.relationship('Note', backref='author', lazy=True)
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)
    study_plans = db.relationship('StudyPlan', backref='user', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(300), nullable=True)
    file_type = db.Column(db.String(20), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    deck_name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    confidence = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    questions_data = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True)
    questions_data = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    goal = db.Column(db.String(300), nullable=True)
    deadline = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── Main Pages ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    notes_count = Note.query.filter_by(user_id=current_user.id).count()
    flashcard_count = Flashcard.query.filter_by(user_id=current_user.id).count()
    quiz_results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.created_at.desc()).limit(5).all()
    avg_score = 0
    all_results = QuizResult.query.filter_by(user_id=current_user.id).all()
    if all_results:
        avg_score = round(sum(r.score / r.total * 100 for r in all_results) / len(all_results))
    return render_template('dashboard.html', notes_count=notes_count,
                           flashcard_count=flashcard_count, quiz_results=quiz_results,
                           avg_score=avg_score)

@app.route('/notes')
@login_required
def notes():
    user_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    return render_template('notes.html', notes=user_notes)

@app.route('/notes/create', methods=['POST'])
@login_required
def create_note():
    title = request.form.get('title')
    content = request.form.get('content')
    note = Note(title=title, content=content, user_id=current_user.id)
    db.session.add(note)
    db.session.commit()
    return jsonify({'success': True, 'id': note.id})

@app.route('/notes/<int:note_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def note_detail(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    if request.method == 'GET':
        return jsonify({'id': note.id, 'title': note.title, 'content': note.content, 'summary': note.summary})
    elif request.method == 'PUT':
        data = request.get_json()
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        note.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        from ai.ocr_reader import extract_text_from_file
        file = request.files.get('file')
        title = request.form.get('title', 'Uploaded Note')
        if file:
            filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            text = extract_text_from_file(filepath)
            note = Note(title=title, content=text, file_path=filename,
                        file_type=file.filename.rsplit('.', 1)[-1].lower(),
                        user_id=current_user.id)
            db.session.add(note)
            db.session.commit()
            return jsonify({'success': True, 'note_id': note.id, 'text': text[:500]})
    return render_template('upload.html')

@app.route('/chat')
@login_required
def chat():
    history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(50).all()
    history.reverse()
    return render_template('chat.html', history=history)

@app.route('/chat/send', methods=['POST'])
@login_required
def chat_send():
    from ai.ai_chat import get_chat_response
    data = request.get_json()
    user_msg = data.get('message', '')
    history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.asc()).limit(20).all()
    msg_history = [{'role': m.role, 'content': m.content} for m in history]
    response = get_chat_response(user_msg, msg_history)
    user_record = ChatMessage(role='user', content=user_msg, user_id=current_user.id)
    ai_record = ChatMessage(role='assistant', content=response, user_id=current_user.id)
    db.session.add(user_record)
    db.session.add(ai_record)
    db.session.commit()
    return jsonify({'response': response})

@app.route('/summary', methods=['POST'])
@login_required
def summarize():
    from ai.ai_summary import generate_summary
    data = request.get_json()
    text = data.get('text', '')
    note_id = data.get('note_id')
    summary = generate_summary(text)
    if note_id:
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        if note:
            note.summary = summary
            db.session.commit()
    return jsonify({'summary': summary})

@app.route('/flashcards')
@login_required
def flashcards():
    decks = db.session.query(Flashcard.deck_name, db.func.count(Flashcard.id)).filter_by(
        user_id=current_user.id).group_by(Flashcard.deck_name).all()
    return render_template('flashcards.html', decks=decks)

@app.route('/flashcards/generate', methods=['POST'])
@login_required
def generate_flashcards():
    from ai.ai_flashcards import create_flashcards
    data = request.get_json()
    text = data.get('text', '')
    deck_name = data.get('deck_name', 'My Deck')
    cards = create_flashcards(text)
    for card in cards:
        fc = Flashcard(front=card['front'], back=card['back'],
                       deck_name=deck_name, user_id=current_user.id)
        db.session.add(fc)
    db.session.commit()
    return jsonify({'success': True, 'count': len(cards)})

@app.route('/flashcards/deck/<deck_name>')
@login_required
def get_deck(deck_name):
    cards = Flashcard.query.filter_by(user_id=current_user.id, deck_name=deck_name).all()
    return jsonify([{'id': c.id, 'front': c.front, 'back': c.back, 'confidence': c.confidence} for c in cards])

@app.route('/flashcards/confidence', methods=['POST'])
@login_required
def update_confidence():
    data = request.get_json()
    card = Flashcard.query.filter_by(id=data.get('id'), user_id=current_user.id).first()
    if card:
        card.confidence = data.get('confidence', 0)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/quiz')
@login_required
def quiz():
    results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.created_at.desc()).limit(10).all()
    return render_template('notes.html', quiz_results=results)

@app.route('/quiz/generate', methods=['POST'])
@login_required
def generate_quiz():
    from ai.ai_quiz import create_quiz
    data = request.get_json()
    text = data.get('text', '')
    topic = data.get('topic', 'General')
    num_questions = int(data.get('num_questions', 5))
    questions = create_quiz(text, num_questions)
    return jsonify({'questions': questions, 'topic': topic})

@app.route('/quiz/submit', methods=['POST'])
@login_required
def submit_quiz():
    data = request.get_json()
    score = data.get('score', 0)
    total = data.get('total', 0)
    topic = data.get('topic', 'General')
    questions_data = json.dumps(data.get('questions', []))
    result = QuizResult(topic=topic, score=score, total=total,
                        questions_data=questions_data, user_id=current_user.id)
    db.session.add(result)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/exam')
@login_required
def exam():
    results = ExamResult.query.filter_by(user_id=current_user.id).order_by(ExamResult.created_at.desc()).limit(10).all()
    return render_template('exam.html', results=results)

@app.route('/exam/generate', methods=['POST'])
@login_required
def generate_exam():
    from ai.ai_exam import create_exam
    data = request.get_json()
    text = data.get('text', '')
    topic = data.get('topic', 'General')
    duration = int(data.get('duration', 30))
    questions = create_exam(text, duration)
    return jsonify({'questions': questions, 'topic': topic, 'duration': duration})

@app.route('/exam/submit', methods=['POST'])
@login_required
def submit_exam():
    data = request.get_json()
    result = ExamResult(topic=data.get('topic', 'Exam'),
                        score=data.get('score', 0), total=data.get('total', 0),
                        duration_minutes=data.get('duration'), user_id=current_user.id)
    db.session.add(result)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/planner')
@login_required
def planner():
    plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.created_at.desc()).all()
    return render_template('planner.html', plans=plans)

@app.route('/planner/generate', methods=['POST'])
@login_required
def generate_plan():
    from ai.ai_coach import generate_study_plan
    data = request.get_json()
    goal = data.get('goal', '')
    deadline = data.get('deadline', '')
    subjects = data.get('subjects', '')
    hours_per_day = data.get('hours_per_day', 2)
    plan_text = generate_study_plan(goal, deadline, subjects, hours_per_day)
    plan = StudyPlan(title=f"Plan: {goal[:50]}", content=plan_text,
                     goal=goal, deadline=deadline, user_id=current_user.id)
    db.session.add(plan)
    db.session.commit()
    return jsonify({'plan': plan_text, 'id': plan.id})

@app.route('/coach')
@login_required
def coach():
    quiz_results = QuizResult.query.filter_by(user_id=current_user.id).all()
    exam_results = ExamResult.query.filter_by(user_id=current_user.id).all()
    return render_template('coach.html', quiz_results=quiz_results, exam_results=exam_results)

@app.route('/coach/advice', methods=['POST'])
@login_required
def get_advice():
    from ai.ai_coach import get_coaching_advice
    quiz_results = QuizResult.query.filter_by(user_id=current_user.id).all()
    performance_data = [{'topic': r.topic, 'score': r.score, 'total': r.total} for r in quiz_results]
    advice = get_coaching_advice(performance_data)
    return jsonify({'advice': advice})

@app.route('/analytics')
@login_required
def analytics():
    quiz_results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.created_at.asc()).all()
    exam_results = ExamResult.query.filter_by(user_id=current_user.id).order_by(ExamResult.created_at.asc()).all()
    notes_count = Note.query.filter_by(user_id=current_user.id).count()
    flashcard_count = Flashcard.query.filter_by(user_id=current_user.id).count()
    return render_template('analytics.html', quiz_results=quiz_results,
                           exam_results=exam_results, notes_count=notes_count,
                           flashcard_count=flashcard_count)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    users = User.query.all()
    total_notes = Note.query.count()
    total_quizzes = QuizResult.query.count()
    return render_template('admin.html', users=users, total_notes=total_notes, total_quizzes=total_quizzes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
