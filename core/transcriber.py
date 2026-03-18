"""
Voice note transcription pipeline — powered by Gemini.

Gemini handles the full pipeline in a single multimodal call:
  - Speech-to-text (audio → text)
  - Arabic correction and Lebanese dialect normalisation
  - Translation to English (if Arabic)
  - 1-2 sentence summary
  - Lebanese location detection
"""

import json
import os
import re
import tempfile
from typing import Dict, Optional

from dotenv import load_dotenv
load_dotenv('.env.txt')

_API_KEY: str = os.getenv('GEMINI_API_KEY', '').strip()
MODEL = 'gemini-2.5-flash'


def _is_arabic(text: str) -> bool:
    if not text:
        return False
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
    return arabic_count / max(len(text), 1) > 0.15


def _gemini_key(override: Optional[str] = None) -> str:
    return (override or _API_KEY).strip()


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "voice_note.ogg",
    claude_api_key: Optional[str] = None,  # kept for API compatibility — ignored
    api_key: Optional[str] = None,
) -> Dict:
    """
    Transcribe a voice note using Gemini multimodal API.

    Returns:
        transcription    : cleaned transcript (Arabic or English)
        translation      : English translation (Arabic notes only, else None)
        summary          : 1-2 sentence English summary
        location_detected: detected Lebanese location(s) or None
        language         : detected language code
        is_arabic        : bool
        engine           : 'Gemini 2.0 Flash'
    """
    key = _gemini_key(api_key)
    if not key:
        return {
            "transcription": "", "translation": None, "summary": None,
            "location_detected": None, "language": "unknown",
            "is_arabic": False, "engine": "unavailable — no Gemini API key",
        }

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        # Determine MIME type
        ext = os.path.splitext(filename)[-1].lower()
        mime = {
            '.ogg': 'audio/ogg', '.opus': 'audio/ogg',
            '.mp3': 'audio/mp3', '.m4a': 'audio/mp4',
            '.aac': 'audio/aac', '.wav': 'audio/wav',
        }.get(ext, 'audio/ogg')

        prompt = (
            "You are an expert transcriber specialising in Lebanese Arabic (عامية لبنانية) "
            "in a construction and building-materials sales context (stamped concrete, flooring, "
            "contractors, project sites, prices per m2, concrete specs).\n\n"
            "Listen carefully to this WhatsApp voice note and:\n"
            "1. Transcribe EXACTLY what is said — preserve Lebanese dialect words "
            "   (e.g. شو، هيدا، عم، رح، فيني، منيح، كتير، عنا).\n"
            "2. Spell out numbers, areas (m2), and prices as spoken.\n"
            "3. Detect ANY Lebanese location — cities, towns, neighbourhoods, districts, "
            "   streets, landmarks (e.g. بيروت، جونيه، ذبية، الأشرفية، المتن، طرابلس، "
            "   صيدا، زحلة، بعلبك، جبيل، عاليه، الشوف, Dbayeh, Jounieh, Metn, Ashrafieh, "
            "   Chouf, Batroun, Fanar, Mansourieh, Verdun, Hamra, Hazmieh, etc.).\n"
            "4. If the speaker mixes Arabic and English/French, keep each word in its "
            "   original language.\n\n"
            "Return ONLY valid JSON (no markdown fences, no extra text):\n"
            "{\n"
            '  "transcription": "full verbatim transcript in original language(s)",\n'
            '  "translation": "English translation of full transcript (if Arabic/French), else null",\n'
            '  "summary": "1-2 sentence English summary: what does the speaker want or say?",\n'
            '  "location_detected": "all Lebanese locations mentioned comma-separated, or null",\n'
            '  "language": "ar | en | fr | mixed | unknown"\n'
            "}"
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                prompt,
            ],
        )

        raw = response.text.strip()
        # Strip markdown fences if Gemini adds them
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE).strip()

        result = json.loads(raw)
        transcription = result.get("transcription") or ""
        is_arabic     = _is_arabic(transcription) or result.get("language") in ("ar", "arabic")

        return {
            "transcription":     transcription,
            "translation":       result.get("translation") or None,
            "summary":           result.get("summary") or None,
            "location_detected": result.get("location_detected") or None,
            "language":          result.get("language", "unknown"),
            "is_arabic":         is_arabic,
            "engine":            "Gemini 2.0 Flash",
        }

    except Exception as e:
        return {
            "transcription": "", "translation": None,
            "summary": f"Transcription failed: {e}",
            "location_detected": None, "language": "unknown",
            "is_arabic": False, "engine": "Gemini 2.0 Flash (error)",
        }


def format_transcription_display(result: Dict) -> str:
    """Format transcription result for Streamlit markdown display."""
    text        = result.get("transcription", "")
    translation = result.get("translation")
    summary     = result.get("summary")
    location    = result.get("location_detected")
    is_arabic   = result.get("is_arabic", False)
    engine      = result.get("engine", "")

    lines = []
    if is_arabic and text:
        lines.append(f"**[Arabic voice note]**\n\n> {text}")
        if translation:
            lines.append(f"\n*[EN] {translation}*")
    elif text:
        lines.append(f"**[Voice note]** {text}")
    else:
        lines.append("*[Voice note — transcription unavailable]*")

    if summary:
        lines.append(f"\n**Summary:** {summary}")
    if location:
        lines.append(f"\n**Location:** {location}")
    if engine:
        lines.append(f"\n<small style='color:#aaa'>Engine: {engine}</small>")

    return "\n".join(lines)
