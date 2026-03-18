"""
WhatsApp .txt / _chat.txt export parser.

Supported timestamp formats:
  iOS plain:    [DD/MM/YYYY, HH:MM:SS] Sender: message
  iOS media:    [YYYY-MM-DD, H:MM:SS AM/PM] Sender: <attached: file>
  Android:      DD/MM/YYYY, HH:MM - Sender: message

Handles:
  - Multi-line messages
  - <attached: filename> media markers (full media exports)
  - <Media omitted> / audio omitted / etc. (text-only exports)
  - Leading Unicode direction marks (U+200E, U+202A, U+202C, U+FEFF)
  - ~ prefix on sender names (WhatsApp Business)
  - AM/PM times
"""

import re
import os
from typing import List, Tuple, Optional, Dict
from datetime import datetime

from core.models import ParsedMessage, ParsedChat

# ── Unicode noise that WhatsApp injects ──────────────────────────────────────
# U+200E LTR mark, U+200F RTL mark, U+202A/C embedding, U+FEFF BOM, U+00A0 NBSP
_UNICODE_NOISE = re.compile(r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff\u00a0]')

def _strip_noise(s: str) -> str:
    return _UNICODE_NOISE.sub('', s).strip()

# ── Timestamp patterns ────────────────────────────────────────────────────────

# iOS full-media export: [2026-02-26, 2:45:59 PM] Sender: body
IOS_ISO_PATTERN = re.compile(
    r'^\[(\d{4}-\d{2}-\d{2}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*[APap][Mm])\]\s*([^:]+?):[^\S\n]*(.*)',
    re.MULTILINE,
)

# iOS plain export: [26/02/2026, 14:45:59] Sender: body
IOS_PATTERN = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\]\s*([^:]+?):[^\S\n]*(.*)',
    re.MULTILINE,
)

# Android: 26/02/2026, 14:45 - Sender: body
ANDROID_PATTERN = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?:\u202f?\s*[APap][Mm])?)\s*[-\u2013]\s*([^:]+?):[^\S\n]*(.*)',
    re.MULTILINE,
)

# ── Media markers ─────────────────────────────────────────────────────────────

# <attached: filename>  — full media export
ATTACHED_PATTERN = re.compile(r'<attached:\s*([^>]+)>', re.IGNORECASE)

# text-only omission phrases
MEDIA_MARKERS = re.compile(
    r'(<Media omitted>|image omitted|audio omitted|video omitted|'
    r'Voice message omitted|sticker omitted|document omitted|'
    r'This message was deleted)',
    re.IGNORECASE,
)

def _extract_attached_filename(body: str) -> Optional[str]:
    """Return filename from <attached: filename> or None."""
    m = ATTACHED_PATTERN.search(body)
    return m.group(1).strip() if m else None

def _is_voice_note(filename: Optional[str], body: str) -> bool:
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        return ext in ('.opus', '.ogg', '.mp3', '.m4a', '.aac')
    return bool(re.search(r'Voice message omitted|audio omitted', body, re.IGNORECASE))

def _is_media_file(filename: Optional[str], body: str) -> bool:
    if filename:
        return True   # any attached file counts as media
    return bool(MEDIA_MARKERS.search(body))

# ── Date / time normalisation ─────────────────────────────────────────────────

def _normalise_timestamp(date_str: str, time_str: str) -> str:
    """Return ISO-8601 'YYYY-MM-DD HH:MM:SS'."""
    time_str = _strip_noise(time_str).replace('\u202f', ' ').strip()

    # Date: already YYYY-MM-DD ?
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        pass   # already ISO
    else:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Time: try AM/PM first, then 24-hour
    for fmt in ('%I:%M:%S %p', '%I:%M %p', '%H:%M:%S', '%H:%M'):
        try:
            t = datetime.strptime(time_str.strip(), fmt)
            return f"{date_str} {t.strftime('%H:%M:%S')}"
        except ValueError:
            continue

    # Fallback: ensure HH:MM:SS shape
    parts = time_str.split(':')
    if len(parts) == 2:
        time_str += ':00'
    return f"{date_str} {time_str}"

# ── Chat name inference ───────────────────────────────────────────────────────

def _infer_chat_name(folder_or_file: str) -> str:
    """
    Infer a human-readable chat name from:
      - a folder like "WhatsApp Chat - +961 3 738 335"
      - a file like "WhatsApp Chat with Rami Khoury.txt"
    """
    base = os.path.basename(folder_or_file.rstrip('/\\'))
    base = os.path.splitext(base)[0]

    # "with Name"
    m = re.search(r'(?:with|With)\s+(.+)', base)
    if m:
        return m.group(1).strip()

    # "WhatsApp Chat - Name / Number"
    cleaned = re.sub(r'^WhatsApp\s+Chat\s*[-–]\s*', '', base, flags=re.IGNORECASE)
    return cleaned.strip() or base

# ── Platform detection ────────────────────────────────────────────────────────

def _detect_platform(text: str) -> Tuple[str, re.Pattern]:
    clean = _strip_noise(text)
    if IOS_ISO_PATTERN.search(clean):
        return 'ios', IOS_ISO_PATTERN
    if IOS_PATTERN.search(clean):
        return 'ios', IOS_PATTERN
    if ANDROID_PATTERN.search(clean):
        return 'android', ANDROID_PATTERN
    return 'unknown', IOS_ISO_PATTERN

# ── Main parse function ───────────────────────────────────────────────────────

def parse_file(filename: str, raw_text: str) -> ParsedChat:
    """
    Parse a WhatsApp .txt / _chat.txt export into a ParsedChat.
    filename is used only for chat_name inference and can be a folder path.
    """
    # Strip Unicode noise from the whole text before pattern matching
    clean_text = _UNICODE_NOISE.sub('', raw_text)

    platform, pattern = _detect_platform(clean_text)
    chat_name = _infer_chat_name(filename)

    matches = list(pattern.finditer(clean_text))
    messages: List[ParsedMessage] = []

    for i, match in enumerate(matches):
        date_str, time_str, sender, body = match.groups()
        timestamp = _normalise_timestamp(date_str.strip(), time_str.strip())

        # Strip sender noise (~ prefix used by WhatsApp Business)
        sender = _strip_noise(sender).lstrip('~').strip()

        # Gather continuation lines
        end = match.end()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
        continuation = clean_text[end:next_start].strip()
        if continuation:
            body = body + '\n' + continuation

        body = _strip_noise(body).strip()

        # Skip system messages (encryption notice, etc.) and empty-body messages
        if not sender or not body.strip() or re.match(
            r'(Messages and calls are end-to-end|‎?Your security code)',
            body, re.IGNORECASE
        ):
            continue

        attached_file = _extract_attached_filename(body)
        is_voice = _is_voice_note(attached_file, body)
        is_media = _is_media_file(attached_file, body)

        messages.append(ParsedMessage(
            seq=i,
            timestamp=timestamp,
            sender=sender,
            body=body,
            is_media=is_media,
            is_voice_note=is_voice,
            attached_filename=attached_file,
        ))

    return ParsedChat(
        filename=filename,
        chat_name=chat_name,
        platform=platform,
        messages=messages,
        raw_text=raw_text,
    )


def scan_export_folders(root: str) -> List[Dict]:
    """
    Scan a directory for WhatsApp export folders (contain _chat.txt).
    Returns list of {folder_path, chat_name, has_media, media_count}.
    """
    results = []
    try:
        for entry in os.scandir(root):
            if not entry.is_dir():
                continue
            chat_txt = os.path.join(entry.path, '_chat.txt')
            if os.path.exists(chat_txt):
                media_files = [
                    f for f in os.listdir(entry.path)
                    if not f.startswith('_') and not f.startswith('.')
                ]
                results.append({
                    'folder_path': entry.path,
                    'chat_name': _infer_chat_name(entry.name),
                    'has_media': len(media_files) > 0,
                    'media_count': len(media_files),
                    'folder_name': entry.name,
                })
    except PermissionError:
        pass
    return results
