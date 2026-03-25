"""
Azure Speech Services — STT and TTS.
Adapted from voice_bot/core/speech.py with graceful degradation.
"""

import os
import io
import base64
import tempfile
from core.config import settings

VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
}


def detect_language_from_text(text: str) -> str:
    """Detect if text is primarily Hindi or English."""
    hindi_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    ratio = hindi_chars / max(len(text), 1)
    return "hi" if ratio > 0.15 else "en"


def speech_to_text(audio_bytes: bytes, audio_format: str = "webm") -> str | None:
    """Convert audio bytes to text using Azure Speech SDK."""
    if not settings.speech_configured:
        return None

    try:
        import azure.cognitiveservices.speech as speechsdk
        from pydub import AudioSegment

        # Convert to WAV 16kHz mono
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=audio_format)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio.export(tmp.name, format="wav")
            wav_path = tmp.name

        config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
        )
        config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
            "Continuous",
        )

        auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=["en-IN", "hi-IN"]
        )
        audio_cfg = speechsdk.AudioConfig(filename=wav_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=config,
            audio_config=audio_cfg,
            auto_detect_source_language_config=auto_detect,
        )

        result = recognizer.recognize_once_async().get()
        try:
            os.unlink(wav_path)
        except Exception:
            pass  # Windows may lock temp file; ignore

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return None

    except Exception as e:
        print(f"[STT] Error: {e}")
        return None


def text_to_speech(text: str, language: str = "en") -> str | None:
    """Convert text to base64-encoded MP3 using Azure Speech SDK."""
    if not settings.speech_configured:
        return None

    try:
        import azure.cognitiveservices.speech as speechsdk

        voice = VOICES.get(language, VOICES["en"])
        config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
        )
        config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )

        ssml = f"""<speak version='1.0' xml:lang='{'hi-IN' if language == 'hi' else 'en-IN'}'>
  <voice name='{voice}'>
    <prosody rate='0.92'>{text}</prosody>
  </voice>
</speak>"""

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            audio_cfg = speechsdk.AudioConfig(filename=tmp.name)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=config, audio_config=audio_cfg
            )
            result = synthesizer.speak_ssml_async(ssml).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                with open(tmp.name, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                os.unlink(tmp.name)
                return b64

        return None
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return None
