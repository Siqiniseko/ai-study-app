-- StudyMind AI Platform — Database Schema
-- SQLite compatible. Flask-SQLAlchemy will auto-create these tables via db.create_all()
-- This file is for reference / manual setup with other databases.

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    file_path VARCHAR(300),
    file_type VARCHAR(20),
    summary TEXT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES user(id),
    session_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flashcard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    deck_name VARCHAR(200) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES user(id),
    confidence INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic VARCHAR(200) NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    questions_data TEXT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic VARCHAR(200) NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    duration_minutes INTEGER,
    questions_data TEXT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    goal VARCHAR(300),
    deadline VARCHAR(100),
    user_id INTEGER NOT NULL REFERENCES user(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
