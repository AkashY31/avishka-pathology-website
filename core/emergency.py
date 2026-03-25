"""Emergency keyword detection — triggers 112 advisory."""

EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe",
    "difficulty breathing", "stroke", "unconscious", "fainted",
    "seizure", "severe bleeding", "not waking up", "overdose",
    "saans nahi", "dil ka dora", "behosh", "stroke",
]

EMERGENCY_RESPONSE_EN = (
    "⚠️ This sounds like a medical emergency. "
    "Please call **112** immediately or go to the nearest hospital. "
    "Do not wait — your life matters more than any test."
)

EMERGENCY_RESPONSE_HI = (
    "⚠️ यह एक चिकित्सा आपातकाल लग रहा है। "
    "कृपया तुरंत **112** पर कॉल करें या नजदीकी अस्पताल जाएं। "
    "देर न करें — आपकी जान सबसे महत्वपूर्ण है।"
)


def check_emergency(text: str) -> tuple[bool, str]:
    """
    Returns (is_emergency, response_message).
    Detects language from Devanagari character ratio.
    """
    lower = text.lower()
    is_emergency = any(kw in lower for kw in EMERGENCY_KEYWORDS)

    if not is_emergency:
        return False, ""

    # Rough language detection
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    is_hindi = (hindi_chars / max(len(text), 1)) > 0.15

    return True, EMERGENCY_RESPONSE_HI if is_hindi else EMERGENCY_RESPONSE_EN
