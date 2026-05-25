// Utilities

function showAlert(message, type = 'success') {
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;max-width:360px;animation:fadeUp 0.3s ease';
  alert.textContent = message;
  document.body.appendChild(alert);
  setTimeout(() => alert.remove(), 3000);
}

function setLoading(btn, loading) {
  if (loading) {
    btn._originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="loading-spinner"></span>';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._originalHTML;
    btn.disabled = false;
  }
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

// Modals

function openModal(id) {
  document.getElementById(id)?.classList.add('active');
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove('active');
}

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

// Chat

const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
let voiceOutputEnabled = false;
let recognition = null;
let listening = false;

if (chatInput) {
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
  });
}

function appendMessage(role, content) {
  const msg = document.createElement('div');
  msg.className = `message ${role === 'user' ? 'user-message' : ''}`;
  const isAI = role !== 'user';
  msg.innerHTML = `
    <div class="message-avatar ${isAI ? 'ai-avatar' : 'user-avatar-msg'}">
      ${isAI ? 'AI' : 'U'}
    </div>
    <div class="message-bubble">${formatMessage(content)}</div>
  `;
  chatMessages?.appendChild(msg);
  chatMessages?.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
  return msg;
}

function formatMessage(text) {
  if (String(text || '').includes('thinking-dots')) return text;
  const safeText = String(text || "")
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return safeText
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

function plainTextFromMessage(text) {
  return String(text || '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`(.*?)`/g, '$1')
    .replace(/[#>-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function updateTutorStatus(sourceCounts, trainedAt) {
  const status = document.getElementById('tutorStatusText');
  if (!status) return;
  const baseLessons = sourceCounts?.base_lessons || 0;
  const notes = sourceCounts?.notes || 0;
  const flashcards = sourceCounts?.flashcards || 0;
  const chunks = sourceCounts?.chunks || 0;
  const trained = trainedAt ? ` Last trained ${new Date(trainedAt).toLocaleString()}.` : '';
  status.textContent = `Trained on ${baseLessons} built-in lesson${baseLessons === 1 ? '' : 's'}, ${notes} note${notes === 1 ? '' : 's'}, ${flashcards} flashcard${flashcards === 1 ? '' : 's'}, and ${chunks} study chunk${chunks === 1 ? '' : 's'}.${trained}`;
}

async function trainTutorModel() {
  const btn = document.getElementById('trainTutorBtn');
  if (btn) setLoading(btn, true);
  try {
    const data = await apiPost('/chat/train', {});
    if (data.success) {
      updateTutorStatus(data.source_counts, data.trained_at);
      showAlert('Tutor trained on your notes and flashcards.');
    } else {
      showAlert('Tutor training failed. Please try again.', 'error');
    }
  } catch {
    showAlert('Tutor training failed. Please try again.', 'error');
  } finally {
    if (btn) setLoading(btn, false);
  }
}

function toggleVoiceOutput() {
  voiceOutputEnabled = !voiceOutputEnabled;
  const btn = document.getElementById('voiceToggleBtn');
  if (btn) {
    btn.classList.toggle('is-active', voiceOutputEnabled);
    btn.setAttribute('aria-label', voiceOutputEnabled ? 'Turn spoken responses off' : 'Turn spoken responses on');
    btn.setAttribute('title', voiceOutputEnabled ? 'Turn spoken responses off' : 'Turn spoken responses on');
  }
  if (!voiceOutputEnabled && window.speechSynthesis) window.speechSynthesis.cancel();
}

function speakTutorResponse(text) {
  if (!voiceOutputEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(plainTextFromMessage(text));
  utterance.rate = 0.96;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;
  const instance = new SpeechRecognition();
  instance.lang = 'en-US';
  instance.interimResults = true;
  instance.continuous = false;

  instance.onstart = () => {
    listening = true;
    document.getElementById('micBtn')?.classList.add('btn-danger');
    const status = document.getElementById('voiceStatus');
    if (status) status.textContent = 'Listening... speak your question.';
  };

  instance.onresult = event => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript)
      .join('');
    if (chatInput) chatInput.value = transcript;
  };

  instance.onerror = () => {
    showAlert('Voice input is not available in this browser session.', 'error');
  };

  instance.onend = () => {
    listening = false;
    document.getElementById('micBtn')?.classList.remove('btn-danger');
    const status = document.getElementById('voiceStatus');
    if (status) status.textContent = 'Press Enter to send. Shift+Enter for a new line. Use Voice to dictate a question.';
  };

  return instance;
}

function toggleVoiceInput() {
  if (!recognition) recognition = setupSpeechRecognition();
  if (!recognition) {
    showAlert('Voice input is not supported by this browser.', 'error');
    return;
  }
  if (listening) recognition.stop();
  else recognition.start();
}

async function sendMessage() {
  const msg = chatInput?.value.trim();
  if (!msg) return;
  chatInput.value = '';
  chatInput.style.height = 'auto';
  if (chatMessages?.children.length === 1 && chatMessages.children[0].style.textAlign === 'center') {
    chatMessages.innerHTML = '';
  }
  appendMessage('user', msg);

  // Thinking indicator
  const thinking = appendMessage('assistant', '<div class="thinking-dots"><span></span><span></span><span></span></div>');

  try {
    const data = await apiPost('/chat/send', { message: msg });
    thinking.remove();
    appendMessage('assistant', data.response);
    speakTutorResponse(data.response);
  } catch {
    thinking.remove();
    appendMessage('assistant', 'Sorry, something went wrong. Please try again.');
  }
}

// Notes

let activeNoteId = null;
let saveTimeout = null;

async function openNote(id) {
  activeNoteId = id;
  document.querySelectorAll('.note-item').forEach(i => i.classList.remove('active'));
  document.querySelector(`[data-note-id="${id}"]`)?.classList.add('active');

  const data = await fetch(`/notes/${id}`).then(r => r.json());
  document.getElementById('noteTitle').value = data.title;
  document.getElementById('noteContent').value = data.content || '';
  document.getElementById('noteEditor').style.display = 'flex';
  document.getElementById('currentNoteId').value = id;

  if (data.summary) {
    document.getElementById('summaryContent').textContent = data.summary;
    document.getElementById('summaryPanel').style.display = 'block';
  } else {
    document.getElementById('summaryPanel').style.display = 'none';
  }
}

function autoSaveNote() {
  if (!activeNoteId) return;
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    const title = document.getElementById('noteTitle')?.value;
    const content = document.getElementById('noteContent')?.value;
    await fetch(`/notes/${activeNoteId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content })
    });
  }, 1000);
}

async function createNote() {
  const data = await apiPost('/notes/create', { title: 'Untitled Note', content: '' });
  if (data.success) location.reload();
}

async function deleteNote(id) {
  if (!confirm('Delete this note?')) return;
  await fetch(`/notes/${id}`, { method: 'DELETE' });
  location.reload();
}

async function summarizeNote() {
  const content = document.getElementById('noteContent')?.value;
  if (!content) return showAlert('Add some content first!', 'error');
  const btn = document.getElementById('summarizeBtn');
  setLoading(btn, true);
  const data = await apiPost('/summary', { text: content, note_id: activeNoteId });
  setLoading(btn, false);
  document.getElementById('summaryContent').textContent = data.summary;
  document.getElementById('summaryPanel').style.display = 'block';
}

// Flashcards

let currentCards = [];
let currentCardIndex = 0;

function loadDeck(deckName) {
  fetch(`/flashcards/deck/${encodeURIComponent(deckName)}`)
    .then(r => r.json())
    .then(cards => {
      currentCards = cards;
      currentCardIndex = 0;
      document.getElementById('deckViewer').style.display = 'block';
      document.getElementById('deckList').style.display = 'none';
      document.getElementById('currentDeckName').textContent = deckName;
      showCard(0);
    });
}

function showCard(index) {
  if (!currentCards.length) return;
  const card = currentCards[index];
  document.getElementById('cardFront').textContent = card.front;
  document.getElementById('cardBack').textContent = card.back;
  document.getElementById('cardCounter').textContent = `${index + 1} / ${currentCards.length}`;
  document.getElementById('flashcard').classList.remove('flipped');

  const conf = card.confidence || 0;
  document.querySelectorAll('.conf-btn').forEach((btn, i) => {
    btn.classList.toggle('active', i === conf);
  });
}

function flipCard() {
  document.getElementById('flashcard')?.classList.toggle('flipped');
}

function nextCard() {
  if (currentCardIndex < currentCards.length - 1) {
    currentCardIndex++;
    showCard(currentCardIndex);
  }
}

function prevCard() {
  if (currentCardIndex > 0) {
    currentCardIndex--;
    showCard(currentCardIndex);
  }
}

async function setConfidence(level) {
  const card = currentCards[currentCardIndex];
  await apiPost('/flashcards/confidence', { id: card.id, confidence: level });
  card.confidence = level;
  showCard(currentCardIndex);
  setTimeout(nextCard, 400);
}

async function generateFlashcards() {
  const text = document.getElementById('flashcardText')?.value;
  const deckName = document.getElementById('deckName')?.value || 'New Deck';
  if (!text) return showAlert('Please enter some text!', 'error');
  const btn = document.getElementById('generateFlashcardsBtn');
  setLoading(btn, true);
  const data = await apiPost('/flashcards/generate', { text, deck_name: deckName });
  setLoading(btn, false);
  if (data.success) {
    showAlert(`Created ${data.count} flashcards!`);
    closeModal('generateModal');
    location.reload();
  }
}

// Quiz

let quizQuestions = [];
let quizAnswers = {};
let quizTopic = '';

async function generateQuiz() {
  const text = document.getElementById('quizText')?.value;
  const topic = document.getElementById('quizTopic')?.value || 'General';
  const num = document.getElementById('numQuestions')?.value || 5;
  if (!text) return showAlert('Please enter some text!', 'error');
  const btn = document.getElementById('generateQuizBtn');
  setLoading(btn, true);
  const data = await apiPost('/quiz/generate', { text, topic, num_questions: num });
  setLoading(btn, false);
  if (data.questions?.length) {
    quizQuestions = data.questions;
    quizTopic = data.topic;
    quizAnswers = {};
    closeModal('quizSetupModal');
    renderQuiz();
  }
}

function renderQuiz() {
  const container = document.getElementById('quizContainer');
  if (!container) return;
  container.style.display = 'block';
  container.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div style="font-family:var(--font-display);font-size:20px;font-weight:800;color:var(--ink)">Quiz</div>
      <button class="btn btn-primary" id="submitQuizBtn" onclick="submitQuiz()">Submit quiz</button>
    </div>
    ${quizQuestions.map((q, i) => `
    <div class="question-card">
      <div class="question-num">Question ${i + 1}</div>
      <div class="question-text">${q.question}</div>
      <div class="options">
        ${q.options.map((opt, j) => `
          <button class="option-btn" onclick="selectAnswer(${i}, ${j})" data-q="${i}" data-opt="${j}">
            <span class="option-letter">${String.fromCharCode(65+j)}</span>
            ${opt.replace(/^[A-D]\)\s*/, '')}
          </button>
        `).join('')}
      </div>
    </div>
  `).join('')}`;
}

function selectAnswer(qIndex, optIndex) {
  quizAnswers[qIndex] = optIndex;
  document.querySelectorAll(`[data-q="${qIndex}"]`).forEach(btn => btn.classList.remove('selected'));
  document.querySelector(`[data-q="${qIndex}"][data-opt="${optIndex}"]`)?.classList.add('selected');
}

async function submitQuiz() {
  let score = 0;
  quizQuestions.forEach((q, i) => {
    const selected = quizAnswers[i];
    const isCorrect = selected === q.correct;
    if (isCorrect) score++;
    document.querySelectorAll(`[data-q="${i}"]`).forEach((btn, j) => {
      btn.disabled = true;
      if (j === q.correct) btn.classList.add('correct');
      else if (j === selected && !isCorrect) btn.classList.add('incorrect');
    });
  });

  await apiPost('/quiz/submit', { score, total: quizQuestions.length, topic: quizTopic, questions: quizQuestions });
  
  const pct = Math.round(score / quizQuestions.length * 100);
  showAlert(`Quiz complete! Score: ${score}/${quizQuestions.length} (${pct}%)`);
  document.getElementById('submitQuizBtn').style.display = 'none';
}

// Exam

let examQuestions = [];
let examAnswers = {};
let examTopic = '';
let examTimer = null;
let examDuration = 0;

async function generateExam() {
  const text = document.getElementById('examText')?.value;
  const topic = document.getElementById('examTopic')?.value || 'Exam';
  const duration = parseInt(document.getElementById('examDuration')?.value || 30);
  if (!text) return showAlert('Please enter some text!', 'error');
  const btn = document.getElementById('generateExamBtn');
  setLoading(btn, true);
  const data = await apiPost('/exam/generate', { text, topic, duration });
  setLoading(btn, false);
  if (data.questions?.length) {
    examQuestions = data.questions;
    examTopic = data.topic;
    examDuration = duration * 60;
    examAnswers = {};
    closeModal('examSetupModal');
    startExam();
  }
}

function startExam() {
  document.getElementById('examSetup').style.display = 'none';
  document.getElementById('examContainer').style.display = 'block';
  renderExam();
  startTimer();
}

function renderExam() {
  const container = document.getElementById('examQuestions');
  if (!container) return;
  container.innerHTML = examQuestions.map((q, i) => {
    if (q.type === 'true_false') {
      return `
        <div class="question-card">
          <div class="question-num">Q${i+1} / ${q.marks} mark${q.marks > 1 ? 's' : ''}</div>
          <div class="question-text">${q.question}</div>
          <div class="options">
            <button class="option-btn" onclick="selectExamAnswer(${i}, true)" data-q="${i}" data-opt="true">
              <span class="option-letter">T</span> True
            </button>
            <button class="option-btn" onclick="selectExamAnswer(${i}, false)" data-q="${i}" data-opt="false">
              <span class="option-letter">F</span> False
            </button>
          </div>
        </div>`;
    }
    return `
      <div class="question-card">
        <div class="question-num">Q${i+1} / ${q.marks} mark${q.marks > 1 ? 's' : ''}</div>
        <div class="question-text">${q.question}</div>
        <div class="options">
          ${q.options.map((opt, j) => `
            <button class="option-btn" onclick="selectExamAnswer(${i}, ${j})" data-q="${i}" data-opt="${j}">
              <span class="option-letter">${String.fromCharCode(65+j)}</span>
              ${opt.replace(/^[A-D]\)\s*/, '')}
            </button>
          `).join('')}
        </div>
      </div>`;
  }).join('');
}

function selectExamAnswer(qIndex, answer) {
  examAnswers[qIndex] = answer;
  document.querySelectorAll(`[data-q="${qIndex}"]`).forEach(btn => btn.classList.remove('selected'));
  document.querySelector(`[data-q="${qIndex}"][data-opt="${answer}"]`)?.classList.add('selected');
}

function startTimer() {
  let remaining = examDuration;
  const el = document.getElementById('examTimer');
  examTimer = setInterval(() => {
    remaining--;
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    if (el) el.textContent = `${m}:${s.toString().padStart(2, '0')}`;
    if (remaining <= 0) { clearInterval(examTimer); submitExam(); }
    if (remaining <= 300 && el) el.style.color = 'var(--danger)';
  }, 1000);
}

async function submitExam() {
  clearInterval(examTimer);
  let score = 0;
  let total = examQuestions.reduce((acc, q) => acc + (q.marks || 1), 0);
  
  examQuestions.forEach((q, i) => {
    const selected = examAnswers[i];
    let correct = q.type === 'true_false' ? q.correct : q.correct;
    if (selected === correct) score += (q.marks || 1);
  });
  
  const durationUsed = Math.floor((examDuration - (parseInt(document.getElementById('examTimer')?.textContent?.split(':')[0] || 0) * 60)) / 60);
  await apiPost('/exam/submit', { score, total, topic: examTopic, duration: durationUsed });
  
  const pct = Math.round(score / total * 100);
  document.getElementById('examContainer').innerHTML = `
    <div class="card" style="text-align:center;padding:48px">
      <div class="empty-icon" style="margin:0 auto 16px">${pct >= 70 ? 'A' : pct >= 50 ? 'B' : 'R'}</div>
      <div class="font-display" style="font-size:32px;margin-bottom:8px">${score}/${total}</div>
      <div style="font-size:48px;font-weight:700;color:${pct>=70?'var(--accent3)':pct>=50?'var(--warn)':'var(--danger)'}">${pct}%</div>
      <div class="text-muted" style="margin-top:16px">${pct>=70?'Excellent work!':pct>=50?'Good effort. Keep studying.':'Keep going. You will get there.'}</div>
      <a href="/exam" class="btn btn-primary" style="margin-top:24px">Back to Exams</a>
    </div>
  `;
}

// Coach

async function getCoachAdvice() {
  const btn = document.getElementById('adviceBtn');
  if (btn) setLoading(btn, true);
  const data = await apiPost('/coach/advice', {});
  if (btn) setLoading(btn, false);
  const el = document.getElementById('adviceContent');
  if (el) el.innerHTML = formatMessage(data.advice);
}

// Study Planner

async function generatePlan() {
  const goal = document.getElementById('planGoal')?.value;
  const deadline = document.getElementById('planDeadline')?.value;
  const subjects = document.getElementById('planSubjects')?.value;
  const hours = document.getElementById('planHours')?.value || 2;
  if (!goal) return showAlert('Please enter your goal!', 'error');
  const btn = document.getElementById('generatePlanBtn');
  setLoading(btn, true);
  const data = await apiPost('/planner/generate', { goal, deadline, subjects, hours_per_day: hours });
  setLoading(btn, false);
  if (document.getElementById('planResult')) document.getElementById('planResult').style.display = 'block';
  if (document.getElementById('planContent')) document.getElementById('planContent').textContent = data.plan;
  location.reload();
}

// Upload

const dropZone = document.getElementById('dropZone');

if (dropZone) {
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    handleFileUpload(e.dataTransfer.files[0]);
  });
}

async function handleFileUpload(file) {
  if (!file) return;
  const title = document.getElementById('uploadTitle')?.value || file.name;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  
  const btn = document.getElementById('uploadBtn');
  if (btn) setLoading(btn, true);
  document.getElementById('uploadProgress')?.style.setProperty('display', 'block');
  
  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (btn) setLoading(btn, false);
    if (data.success) {
      showAlert('File uploaded and text extracted!');
      document.getElementById('extractedText')?.style.setProperty('display', 'block');
      if (document.getElementById('extractedPreview'))
        document.getElementById('extractedPreview').textContent = data.text + '...';
    }
  } catch (e) {
    if (btn) setLoading(btn, false);
    showAlert('Upload failed. Please try again.', 'error');
  }
}

// Analytics Charts

function initCharts() {
  const scoreCtx = document.getElementById('scoreChart');
  const topicCtx = document.getElementById('topicChart');

  if (scoreCtx && window.quizData) {
    new Chart(scoreCtx, {
      type: 'line',
      data: {
        labels: window.quizData.map((_, i) => `Quiz ${i+1}`),
        datasets: [{
          label: 'Score %',
          data: window.quizData.map(r => Math.round(r.score / r.total * 100)),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, grid: { color: 'rgba(16,24,40,0.08)' }, ticks: { color: '#667085' } },
          x: { grid: { color: 'rgba(16,24,40,0.08)' }, ticks: { color: '#667085' } }
        }
      }
    });
  }

  if (topicCtx && window.topicData) {
    new Chart(topicCtx, {
      type: 'doughnut',
      data: {
        labels: window.topicData.map(t => t.topic),
        datasets: [{
          data: window.topicData.map(t => Math.round(t.score / t.total * 100)),
          backgroundColor: ['#2563eb','#0f766e','#16a34a','#d97706','#dc2626'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { color: '#667085', padding: 16 } } }
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', initCharts);
