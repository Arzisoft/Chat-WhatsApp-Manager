"""
WhatsApp Bridge client — talks to bridge/server.js (whatsapp-web.js).
No Selenium, no DOM scraping. The Node.js bridge handles the QR + session.
"""

import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

BRIDGE_URL = "http://localhost:3001"
BRIDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bridge")

try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ── Bridge process management ─────────────────────────────────────────────────

def bridge_running() -> bool:
    """Return True if the Node bridge is up and responding."""
    if not REQUESTS_AVAILABLE:
        return False
    try:
        r = _requests.get(f"{BRIDGE_URL}/status", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_bridge() -> Optional[subprocess.Popen]:
    """
    Launch `node server.js` in bridge/ as a background process.
    Returns the Popen handle (store in session_state to keep it alive).
    """
    if not os.path.exists(os.path.join(BRIDGE_DIR, "node_modules")):
        raise RuntimeError(
            "Node modules not installed. Run:  cd bridge && npm install"
        )
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=BRIDGE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Give it a moment to start
    time.sleep(3)
    return proc


# ── API helpers ───────────────────────────────────────────────────────────────

def get_status() -> Dict:
    """
    Return {status, qr_image}.
    status: 'connecting' | 'qr' | 'authenticated' | 'ready' | 'disconnected' | 'error'
    qr_image: base64 PNG data-URL or None
    """
    r = _requests.get(f"{BRIDGE_URL}/status", timeout=5)
    r.raise_for_status()
    return r.json()


def get_chats() -> List[Dict]:
    """Return list of chats: [{id, name, is_group, timestamp, unread}]."""
    r = _requests.get(f"{BRIDGE_URL}/chats", timeout=15)
    r.raise_for_status()
    return r.json()


def get_messages(chat_id: str, limit: int = 300) -> List[Dict]:
    """
    Fetch messages for a chat.
    Returns [{id, timestamp, from, body, type, is_media, is_voice}]
    """
    r = _requests.get(
        f"{BRIDGE_URL}/messages/{chat_id}",
        params={"limit": limit},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def get_media(message_id: str) -> Dict:
    """Download media for a message. Returns {data (base64), mimetype, filename}."""
    r = _requests.get(f"{BRIDGE_URL}/media/{message_id}", timeout=30)
    r.raise_for_status()
    return r.json()


def disconnect() -> None:
    """Tell the bridge to log out."""
    try:
        _requests.post(f"{BRIDGE_URL}/disconnect", timeout=10)
    except Exception:
        pass


# ── Message → ParsedMessage converter ────────────────────────────────────────

def messages_to_raw_text(messages: List[Dict], chat_name: str = "") -> str:
    """Convert bridge message list to the same plain-text format the parser uses."""
    lines = []
    for m in messages:
        ts = m.get("timestamp", 0)
        try:
            dt = datetime.fromtimestamp(ts).strftime("%m/%d/%Y, %H:%M")
        except Exception:
            dt = "01/01/2025, 00:00"
        sender = m.get("from", "Unknown").split("@")[0]
        body   = m.get("body") or ("<Voice Message>" if m.get("is_voice") else "<Media omitted>")
        lines.append(f"[{dt}] {sender}: {body}")
    return "\n".join(lines)
