"""
Unified Chat Agent — combines RAG retrieval + rule-based fallback + Azure OpenAI.
Handles health queries, test recommendations, booking guidance.
"""

import json
from core.config import settings
from core.openai_client import chat_completion
from core.emergency import check_emergency
from core.test_catalog import recommend_tests, TEST_CATALOG
from core.speech import detect_language_from_text

SYSTEM_PROMPT = """You are Dr. Avi, a warm and knowledgeable AI health assistant at Avishka Pathology Lab.

About Avishka Pathology:
- Founded by Dr. Aman Yadav (Vikas)
- Location: Mahuja Modh, Martinganj, Azamgarh, U.P.
- Phone: +91-7355230710 | Email: avishka.pathology@outlook.com
- Tagline: "Precision Diagnostics at Prices You Can Afford"
- Accreditation: NABL Accredited Lab — highest quality standards guaranteed
- Lab Type: Fully Ultramodern Computerized Lab
- Working Hours: Monday to Sunday, 7:00 AM – 8:00 PM (Open all 7 days)
- Home Collection: Yes, home sample collection is available — call 7355230710 to schedule

Available Tests & Prices:
- Complete Blood Count (CBC): ₹300
- Blood Sugar Fasting: ₹120
- Blood Sugar Post Prandial: ₹120
- Blood Sugar Random: ₹120
- Lipid Profile: ₹350
- Thyroid Profile (T3, T4, TSH): ₹600
- Liver Function Test (LFT): ₹400
- Kidney Function Test (KFT): ₹350
- Urine Routine & Microscopy: ₹100
- Vitamin D: ₹800
- Vitamin B12: ₹600
- HbA1c (Glycated Hemoglobin): ₹350
- ECG / Electrocardiogram: ₹200
- Full Body Checkup Package: Available — ask for pricing

Your role:
1. Answer health and diagnostic test questions with clarity and empathy
2. Recommend appropriate tests based on symptoms described
3. Explain test preparation instructions clearly
4. Mention home collection availability when relevant
5. Guide users to book appointments — direct them to the Booking section or call 7355230710
6. Be concise — 2 to 4 sentences per response unless detail is needed
7. Never diagnose diseases — only suggest tests and advise seeing a doctor
8. Highlight NABL accreditation when patients ask about quality or trust

LANGUAGE RULE (strictly follow):
- English input → reply FULLY in English
- Hindi input (Devanagari) → reply FULLY in Hindi
- Never mix languages in a single response

For emergencies (chest pain, stroke, breathing difficulty), immediately advise calling 112.

VOICE CAPABILITIES (important — answer accurately):
- You DO have voice input: users can click the 🎤 microphone button to speak in Hindi or English (works in Chrome browser)
- You DO have voice output: users can click the 🔊 button to hear your responses spoken aloud
- If a user asks "can you hear me?" or "can you speak?" — tell them YES, voice is supported via the mic 🎤 and speaker 🔊 buttons in the chat widget
- If they are not using Chrome, suggest opening in Chrome for best voice experience"""


def build_messages(history: list[dict], user_message: str, context_chunks: list[str] = None) -> list[dict]:
    """Build the messages array for the OpenAI API call."""
    system = SYSTEM_PROMPT

    # Inject RAG context if available
    if context_chunks:
        context_text = "\n\n".join(context_chunks[:3])
        system += f"\n\nRelevant document context:\n{context_text}"

    messages = [{"role": "system", "content": system}]

    # Add conversation history (last 10 turns)
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    return messages


def get_rule_based_response(user_message: str) -> str | None:
    """
    Fast rule-based responses for common queries without calling the LLM.
    Returns None if no rule matches (falls through to LLM).
    """
    lower = user_message.lower().strip()

    # Greeting
    if any(g in lower for g in ["hello", "hi ", "hey", "namaste", "namaskar", "हेलो", "नमस्ते"]):
        return (
            "Hello! I'm Dr. Avi, your AI health assistant at Avishka Pathology. 😊\n\n"
            "How can I help you today? You can ask me about:\n"
            "• Which tests you need for your symptoms\n"
            "• Test prices and preparation\n"
            "• How to book an appointment"
        )

    # Price / cost queries
    if any(w in lower for w in ["price", "cost", "kitna", "rate", "charge", "fee", "rupee", "₹"]):
        tests_list = "\n".join([
            f"• {v['name']}: ₹{v['price']}"
            for v in TEST_CATALOG.values()
        ])
        return (
            f"Here are our test prices:\n\n{tests_list}\n\n"
            f"🏠 Home collection available | ✅ NABL Accredited\n"
            f"Call 7355230710 for Full Body Package pricing."
        )

    # Timing / hours
    if any(w in lower for w in ["time", "hours", "open", "close", "when", "timing", "समय", "खुलना"]):
        return (
            "🕐 We are open **7 days a week**:\n"
            "Monday to Sunday: 7:00 AM – 8:00 PM\n\n"
            "🏠 Home collection available — call to schedule!\n"
            "📍 Mahuja Modh, Martinganj, Azamgarh | 📞 7355230710"
        )

    # Home collection
    if any(w in lower for w in ["home", "collection", "ghar", "घर"]):
        return (
            "🏠 Yes! We provide **home sample collection** service.\n\n"
            "Just call us at 📞 7355230710 to schedule a home visit "
            "at your convenient time.\n"
            "We are open 7 days a week, 7 AM – 8 PM."
        )

    # NABL / certification
    if any(w in lower for w in ["nabl", "certified", "accredited", "quality", "trust"]):
        return (
            "✅ Yes! Avishka Pathology is **NABL Accredited** — ensuring the highest "
            "standards in diagnostic testing.\n\n"
            "NABL (National Accreditation Board for Testing & Calibration Laboratories) "
            "certification means your reports are accurate and internationally recognized."
        )

    # Address / location
    if any(w in lower for w in ["address", "location", "where", "kahan", "पता", "कहाँ"]):
        return (
            "📍 Avishka Pathology\n"
            "Mahuja Modh, Martinganj, Azamgarh, U.P.\n\n"
            "📞 +91-7355230710\n"
            "📧 avishka.pathology@outlook.com\n\n"
            "✅ NABL Accredited | 🏠 Home Collection Available\n"
            "Founded by Dr. Aman Yadav (Vikas)"
        )

    return None  # Fall through to LLM


def process_message(
    user_message: str,
    history: list[dict],
    rag_retriever=None,
) -> dict:
    """
    Main entry point for chat processing.
    Returns: {reply, language, tests_recommended, is_emergency}
    """
    # Emergency check
    is_emergency, emergency_msg = check_emergency(user_message)
    if is_emergency:
        return {
            "reply": emergency_msg,
            "language": "hi" if "यह" in emergency_msg else "en",
            "tests_recommended": [],
            "is_emergency": True,
        }

    # Detect language
    language = detect_language_from_text(user_message)

    # Fast rule-based response
    rule_reply = get_rule_based_response(user_message)
    if rule_reply:
        return {
            "reply": rule_reply,
            "language": language,
            "tests_recommended": [],
            "is_emergency": False,
        }

    # RAG retrieval
    context_chunks = []
    if rag_retriever:
        try:
            context_chunks = rag_retriever.retrieve(user_message, k=3)
        except Exception:
            pass

    # Build messages and call LLM
    messages = build_messages(history, user_message, context_chunks)
    reply = chat_completion(messages, max_tokens=500)

    # Detect if this is a symptom query and add test recommendations
    tests_recommended = []
    symptom_keywords = [
        "pain", "fatigue", "tired", "fever", "sugar", "thyroid",
        "dizzy", "headache", "weakness", "nausea", "cough", "test",
        "दर्द", "बुखार", "थकान", "सिरदर्द",
    ]
    if any(kw in user_message.lower() for kw in symptom_keywords):
        tests_recommended = recommend_tests(user_message)

    return {
        "reply": reply,
        "language": language,
        "tests_recommended": tests_recommended,
        "is_emergency": False,
    }
