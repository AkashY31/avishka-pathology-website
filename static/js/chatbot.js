/* ============================================================
   AVISHKA PATHOLOGY — Chatbot Widget (Dr. Avi)
   Text + Voice | Session-persisted | RAG-backed
   ============================================================ */

let chatSessionId  = null;
let isRecording    = false;
let mediaRecorder  = null;
let audioChunks    = [];
let chatOpen       = false;
let ttsEnabled     = true;    // ON by default — user clicks 🔊 to mute

// ── Open / Close (FAB toggles the widget) ────────────────────
function toggleChat() {
  chatOpen ? closeChat() : openChat();
}

function openChat() {
  chatOpen = true;
  document.getElementById('chatWidget').classList.add('open');
  document.getElementById('chatFabIcon').textContent = '✕';
  if (!chatSessionId) initChatSession();
  setTimeout(() => document.getElementById('chatInput').focus(), 300);
}

function closeChat() {
  chatOpen = false;
  document.getElementById('chatWidget').classList.remove('open');
  document.getElementById('chatFabIcon').textContent = '🤖';
}

// ── Session init ─────────────────────────────────────────────
async function initChatSession() {
  try {
    const res  = await fetch('/api/chat/session/new', { method: 'POST' });
    const data = await res.json();
    chatSessionId = data.session_id;
    appendBotMessage(data.greeting || getFallbackGreeting());
  } catch {
    appendBotMessage(getFallbackGreeting());
  }
}

function getFallbackGreeting() {
  return (
    "Hello! I'm Dr. Avi, your AI health assistant at Avishka Pathology. 😊\n\n" +
    "You can ask me about test prices, preparation, symptoms, or booking.\n\n" +
    "🎤 Click the mic button to speak (Hindi/English) — works in Chrome\n" +
    "🔊 Voice replies are ON — click 🔊 in the header to mute\n" +
    "📞 For immediate help: 7355230710"
  );
}

// ── Message Rendering ────────────────────────────────────────
function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function appendUserMessage(text) {
  if (!text) return;
  const box = document.getElementById('chatMessages');
  box.innerHTML += `
    <div class="msg user">
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-time">${now()}</div>
    </div>`;
  scrollChat();
  hideQuickButtons();
}

function appendBotMessage(text, testsRecommended = []) {
  // Guard against undefined/null reply
  if (!text || text === 'undefined') {
    text = "I'm having a moment — please try again or call 📞 7355230710.";
  }

  const box = document.getElementById('chatMessages');

  // Convert **bold** and newlines to HTML
  const html = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

  let chipsHtml = '';
  if (Array.isArray(testsRecommended) && testsRecommended.length) {
    const chips = testsRecommended.slice(0,5).map(t =>
      `<button class="test-chip-btn" onclick="bookTestFromChat('${t.code || ''}')">${t.icon || '🔬'} ${t.name || ''} — ₹${t.price || ''}</button>`
    ).join('');
    chipsHtml = `<div class="test-chips" style="margin-top:8px;">${chips}</div>`;
  }

  box.innerHTML += `
    <div class="msg bot">
      <div class="msg-bubble">${html}${chipsHtml}</div>
      <div class="msg-time">${now()}</div>
    </div>`;
  scrollChat();
  speakText(text);  // speak aloud if TTS is enabled
}

function showTyping() {
  document.getElementById('typingBubble').classList.add('show');
  scrollChat();
}
function hideTyping() {
  document.getElementById('typingBubble').classList.remove('show');
}
function scrollChat() {
  const box = document.getElementById('chatMessages');
  box.scrollTop = box.scrollHeight;
}
function hideQuickButtons() {
  document.getElementById('chatQuick').style.display = 'none';
}

// ── Send Text Message ────────────────────────────────────────
async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const text  = (input.value || '').trim();
  if (!text) return;

  input.value = '';
  appendUserMessage(text);
  showTyping();

  try {
    const res = await fetch('/api/chat/message', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text, session_id: chatSessionId }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    const data = await res.json();
    chatSessionId = data.session_id || chatSessionId;
    hideTyping();

    // Guard: reply must be a non-empty string
    const reply = (typeof data.reply === 'string' && data.reply.trim())
      ? data.reply
      : "Sorry, I didn't get a response. Please call 7355230710.";

    appendBotMessage(reply, data.tests_recommended || []);

    if (data.audio_b64) playAudio(data.audio_b64);

  } catch (err) {
    hideTyping();
    appendBotMessage(
      `Sorry, I couldn't connect right now. (${err.message})\n\n` +
      `Please call **7355230710** or try again in a moment.`
    );
  }
}

function chatKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}

function sendQuick(text) {
  if (!text) return;
  document.getElementById('chatInput').value = text;
  sendChatMessage();
}

// ── Voice Recording — Browser Web Speech API (no ffmpeg needed) ──
function toggleMic() {
  if (isRecording) stopRecording();
  else             startRecording();
}

function startRecording() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    appendBotMessage(
      '🎤 Voice input works best in **Chrome** browser.\n\n' +
      'Please open this site in Chrome, or type your question below.'
    );
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous      = false;
  recognition.interimResults  = false;
  recognition.maxAlternatives = 1;
  // Hindi first — Chrome will auto-detect English too
  recognition.lang = 'hi-IN';

  const mic = document.getElementById('micBtn');
  mic.classList.add('recording');
  mic.title       = 'Listening… click to stop';
  mic.textContent = '⏹';
  isRecording = true;
  window._speechRec = recognition;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    stopRecording();
    // Show what was heard, then send as text message
    document.getElementById('chatInput').value = transcript;
    sendChatMessage();
  };

  recognition.onerror = (event) => {
    stopRecording();
    if (event.error === 'not-allowed') {
      appendBotMessage('Microphone access denied. Please allow mic permission in your browser.');
    } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
      appendBotMessage('Could not recognize speech. Please try again or type your question.');
    }
  };

  recognition.onend = () => { stopRecording(); };

  try {
    recognition.start();
  } catch (e) {
    stopRecording();
    appendBotMessage('Could not start voice recognition. Please type your question.');
  }
}

function stopRecording() {
  if (window._speechRec) {
    try { window._speechRec.stop(); } catch {}
    window._speechRec = null;
  }
  isRecording = false;
  const mic = document.getElementById('micBtn');
  mic.classList.remove('recording');
  mic.title       = 'Voice input (Hindi / English)';
  mic.textContent = '🎤';
}

// ── TTS — Browser Web Speech Synthesis ───────────────────────
function toggleTTS() {
  ttsEnabled = !ttsEnabled;
  const btn = document.getElementById('ttsToggleBtn');
  btn.textContent = ttsEnabled ? '🔊' : '🔇';
  btn.title       = ttsEnabled ? 'Voice ON — click to mute' : 'Voice OFF — click to enable';
  btn.style.opacity = ttsEnabled ? '1' : '0.45';
  if (!ttsEnabled) window.speechSynthesis && window.speechSynthesis.cancel();
}

function speakText(text) {
  if (!ttsEnabled) return;
  if (!window.speechSynthesis) return;

  // Strip markdown symbols and emoji for cleaner speech
  const clean = text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/[🔬💉🏠⚡✅📞📅😊🤖₹]/gu, '')
    .replace(/\n+/g, '. ')
    .trim();

  if (!clean) return;

  window.speechSynthesis.cancel(); // stop any previous

  const utter  = new SpeechSynthesisUtterance(clean);
  utter.lang   = 'hi-IN';  // Hindi — Chrome will auto-use English if text is English
  utter.rate   = 0.92;
  utter.pitch  = 1.05;

  // Prefer an Indian voice if available
  const voices = window.speechSynthesis.getVoices();
  const indian = voices.find(v => v.lang === 'hi-IN') ||
                 voices.find(v => v.lang === 'en-IN') ||
                 voices.find(v => v.lang.startsWith('hi')) ||
                 null;
  if (indian) utter.voice = indian;

  window.speechSynthesis.speak(utter);
}

// Legacy — kept for compatibility (Azure TTS b64 no longer used)
function playAudio(b64) {
  // Browser TTS handles speech now; ignore server-side audio_b64
}

// ── Book from Chat ───────────────────────────────────────────
function bookTestFromChat(code) {
  closeChat();
  showPage('booking');
  if (code) setTimeout(() => preSelectTest(code), 500);
}

// Expose globally
window.toggleChat      = toggleChat;
window.openChat        = openChat;
window.closeChat       = closeChat;
window.sendChatMessage = sendChatMessage;
window.sendQuick       = sendQuick;
window.chatKeyDown     = chatKeyDown;
window.toggleMic       = toggleMic;
window.toggleTTS       = toggleTTS;
