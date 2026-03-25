# Avishka Pathology — Unified AI Platform

**Founded by Dr. Aman Yadav (Vikas)**
Mahuja Modh, Martinganj, Azamgarh, U.P. | 📞 7355230710

---

## Quick Start (3 steps)

### 1. Install dependencies
```bash
cd avishka_pathology_website
pip install -r requirements.txt
```

> **Voice features** also require [ffmpeg](https://ffmpeg.org/download.html) installed on your system.

### 2. Configure environment
The `.env` file is already set up. Verify it has your Azure credentials:
```
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-5.3-chat
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus
```

### 3. Run the server
```bash
python main.py
```

**Website is live at → http://localhost:3000**

---

## Project Structure

```
avishka_pathology_website/
├── main.py                  ← FastAPI app entry point (port 3000)
├── requirements.txt
├── .env                     ← Your credentials (never commit this)
│
├── database/
│   ├── models.py            ← SQLAlchemy models (Booking, ChatSession, Contact)
│   └── db.py                ← SQLite engine + get_db dependency
│
├── api/
│   ├── chat.py              ← POST /api/chat/message
│   ├── booking.py           ← POST /api/booking/submit, GET /api/booking/slots
│   ├── voice.py             ← POST /api/voice/transcribe-and-reply
│   ├── contact.py           ← POST /api/contact/submit
│   └── upload.py            ← POST /api/upload/document (RAG PDFs)
│
├── agents/
│   └── chat_agent.py        ← Unified AI chat (RAG + rule-based + LLM)
│
├── rag/
│   ├── indexer.py           ← PDF ingestion → FAISS vector index
│   ├── retriever.py         ← Semantic retrieval for chatbot context
│   └── documents/           ← Place your PDF files here
│
├── core/
│   ├── config.py            ← All settings from .env
│   ├── openai_client.py     ← Azure OpenAI wrapper
│   ├── speech.py            ← Azure STT + TTS
│   ├── emergency.py         ← Emergency keyword detection → 112
│   └── test_catalog.py      ← 13 tests with prices, symptoms map
│
└── static/
    ├── index.html           ← Premium SPA (5 pages)
    ├── css/style.css        ← Full design system (dark/light themes)
    └── js/
        ├── app.js           ← SPA router, theme toggle, counters
        ├── chatbot.js       ← Dr. Avi widget (text + voice)
        └── booking.js       ← 5-step booking form
```

---

## Adding RAG Documents

1. Place any `.pdf` file in `rag/documents/`
2. The index rebuilds automatically on next startup (or after upload)
3. Or use the upload API: `POST /api/upload/document` with a PDF file

The chatbot will use document content to answer patient queries.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat/message` | POST | Send chat message, get AI reply |
| `/api/chat/session/new` | POST | Create new chat session |
| `/api/booking/submit` | POST | Submit appointment request |
| `/api/booking/slots` | GET | Get available time slots |
| `/api/booking/tests` | GET | Get full test catalog |
| `/api/booking/status/{ref}` | GET | Check booking status |
| `/api/voice/transcribe-and-reply` | POST | Voice input → AI reply + TTS |
| `/api/contact/submit` | POST | Submit contact form |
| `/api/upload/document` | POST | Upload PDF for RAG |
| `/api/docs` | GET | Swagger UI |

---

## Architecture

```
Browser (SPA)
    │
    ├── Static pages: Home, Services, About, Contact, Booking
    ├── Chatbot Widget (Dr. Avi) — Text + Voice
    │
    ↓ HTTP
FastAPI (port 3000)
    │
    ├── Chat Agent ──→ Rule-based responses (fast, no API cost)
    │               └→ RAG retrieval (FAISS + LangChain)
    │               └→ Azure OpenAI GPT (full LLM)
    │
    ├── Voice ───────→ Azure Speech STT → Chat Agent → Azure TTS
    │
    ├── Booking ─────→ SQLite DB (persistent)
    └── Contact ─────→ SQLite DB (persistent)
```

---

## Features

- **5-page SPA**: Home, Services, About, Contact, Booking
- **Dark/Light theme** with toggle (persisted in localStorage)
- **Dr. Avi AI Chatbot**: Text + voice, bilingual (Hindi/English)
- **5-step booking**: Symptoms → Test recommendation → Slot → Confirm
- **RAG**: Upload PDFs → chatbot answers from documents
- **SQLite persistence**: Bookings and chat sessions survive restarts
- **Emergency detection**: Auto-detects emergencies → advises calling 112
- **Fully responsive**: Desktop, tablet, mobile
