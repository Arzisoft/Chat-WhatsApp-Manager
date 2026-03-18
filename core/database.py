"""
SQLite database layer.
All DB operations for chats, messages, analyses, contacts, projects, concrete_orders,
action_items, and financial_mentions.
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from core.models import ParsedChat

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'assistant.db')


# ── Connection ───────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT    NOT NULL UNIQUE,
    chat_name       TEXT,
    imported_at     TEXT    NOT NULL,
    raw_text        TEXT,
    message_count   INTEGER DEFAULT 0,
    date_first_msg  TEXT,
    date_last_msg   TEXT,
    platform        TEXT    CHECK(platform IN ('ios','android','unknown','whatsapp-web.js'))
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    timestamp       TEXT    NOT NULL,
    sender          TEXT    NOT NULL,
    body            TEXT    NOT NULL,
    is_media        INTEGER DEFAULT 0,
    is_voice_note   INTEGER DEFAULT 0,
    attached_filename TEXT,
    media_path      TEXT,
    transcription   TEXT,
    translation     TEXT,
    seq             INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id             INTEGER NOT NULL UNIQUE REFERENCES chats(id) ON DELETE CASCADE,
    analyzed_at         TEXT    NOT NULL,
    model_used          TEXT    DEFAULT 'claude-haiku-4-5-20251001',
    primary_area        TEXT,
    secondary_areas     TEXT,
    category            TEXT    CHECK(category IN
                            ('Project','Contractor','Potential Client',
                             'Distributor','Internal/Team','Personal')),
    status              TEXT    CHECK(status IN
                            ('Active','Waiting','Closed','Lost','Follow-up Needed')),
    urgency_level       TEXT    CHECK(urgency_level IN ('Low','Medium','High','Critical')),
    sentiment           TEXT    CHECK(sentiment IN ('Positive','Neutral','Negative','Frustrated')),
    relationship_stage  TEXT    CHECK(relationship_stage IN
                            ('Cold','Warm','Hot','Negotiating','Confirmed','Delivered','Dispute')),
    language_mix        TEXT,
    executive_summary   TEXT,
    timeline_json       TEXT,
    followup_needed     INTEGER DEFAULT 0,
    followup_reason     TEXT,
    followup_action     TEXT,
    negotiation_signals TEXT,
    last_activity_date  TEXT,
    lifecycle_transitions TEXT,
    competitors_mentioned TEXT,
    payment_terms       TEXT,
    payment_method      TEXT,
    payment_outstanding REAL,
    payment_overdue     INTEGER DEFAULT 0,
    raw_claude_json     TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id             INTEGER NOT NULL UNIQUE REFERENCES chats(id) ON DELETE CASCADE,
    name                TEXT,
    phone               TEXT,
    role                TEXT    CHECK(role IN
                            ('Contractor','Developer','Project Manager','Dealer',
                             'Architect','Engineer','Unknown')),
    company             TEXT,
    is_decision_maker   INTEGER DEFAULT 0,
    created_at          TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id             INTEGER NOT NULL UNIQUE REFERENCES chats(id) ON DELETE CASCADE,
    name                TEXT,
    type                TEXT    CHECK(type IN
                            ('Residential','Commercial','Infrastructure','Industrial','Unknown')),
    location_detail     TEXT,
    floors              INTEGER,
    area_m2             REAL,
    total_m3_estimate   REAL,
    start_date          TEXT,
    completion_date     TEXT,
    created_at          TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS concrete_orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    mix_grade       TEXT,
    slump           TEXT,
    pump_required   INTEGER DEFAULT 0,
    volume_m3       REAL,
    price_per_m3    REAL,
    currency        TEXT    DEFAULT 'USD',
    delivery_date   TEXT,
    status          TEXT    CHECK(status IN ('Quoted','Ordered','Delivered','Cancelled')),
    seq             INTEGER
);

CREATE TABLE IF NOT EXISTS action_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    action          TEXT    NOT NULL,
    due_date        TEXT,
    priority        TEXT    CHECK(priority IN ('Low','Medium','High','Critical')),
    completed       INTEGER DEFAULT 0,
    completed_at    TEXT,
    created_at      TEXT    NOT NULL,
    seq             INTEGER
);

CREATE TABLE IF NOT EXISTS financial_mentions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    mention_date    TEXT,
    mention_type    TEXT    CHECK(mention_type IN
                        ('price_per_m3','total_order','volume_m3','quote',
                         'discount','delivery_cost','payment_terms','complaint','other')),
    amount          REAL,
    currency        TEXT    DEFAULT 'USD',
    raw_text        TEXT,
    context_note    TEXT,
    seq             INTEGER
);

CREATE INDEX IF NOT EXISTS idx_analyses_area        ON analyses(primary_area);
CREATE INDEX IF NOT EXISTS idx_analyses_status      ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_category    ON analyses(category);
CREATE INDEX IF NOT EXISTS idx_contacts_role        ON contacts(role);
CREATE INDEX IF NOT EXISTS idx_projects_type        ON projects(type);
CREATE INDEX IF NOT EXISTS idx_concrete_orders_chat ON concrete_orders(chat_id);
CREATE INDEX IF NOT EXISTS idx_action_items_chat    ON action_items(chat_id);
CREATE INDEX IF NOT EXISTS idx_action_items_done    ON action_items(completed);
"""


def init_db() -> None:
    """Create all tables and apply any pending migrations."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
    _migrate()


def _migrate() -> None:
    """Non-destructive column additions for existing DBs."""
    migrations = [
        # messages table
        ("messages", "is_voice_note",       "ALTER TABLE messages ADD COLUMN is_voice_note INTEGER DEFAULT 0"),
        ("messages", "attached_filename",   "ALTER TABLE messages ADD COLUMN attached_filename TEXT"),
        ("messages", "media_path",          "ALTER TABLE messages ADD COLUMN media_path TEXT"),
        ("messages", "transcription",       "ALTER TABLE messages ADD COLUMN transcription TEXT"),
        ("messages", "translation",         "ALTER TABLE messages ADD COLUMN translation TEXT"),
        ("messages", "vn_summary",          "ALTER TABLE messages ADD COLUMN vn_summary TEXT"),
        ("messages", "vn_location",         "ALTER TABLE messages ADD COLUMN vn_location TEXT"),
        # analyses table — new fields
        ("analyses", "sentiment",           "ALTER TABLE analyses ADD COLUMN sentiment TEXT"),
        ("analyses", "relationship_stage",  "ALTER TABLE analyses ADD COLUMN relationship_stage TEXT"),
        ("analyses", "language_mix",        "ALTER TABLE analyses ADD COLUMN language_mix TEXT"),
        ("analyses", "competitors_mentioned","ALTER TABLE analyses ADD COLUMN competitors_mentioned TEXT"),
        ("analyses", "payment_terms",       "ALTER TABLE analyses ADD COLUMN payment_terms TEXT"),
        ("analyses", "payment_method",      "ALTER TABLE analyses ADD COLUMN payment_method TEXT"),
        ("analyses", "payment_outstanding", "ALTER TABLE analyses ADD COLUMN payment_outstanding REAL"),
        ("analyses", "payment_overdue",     "ALTER TABLE analyses ADD COLUMN payment_overdue INTEGER DEFAULT 0"),
    ]
    with get_connection() as conn:
        for table, col, sql in migrations:
            exists = conn.execute(
                f"SELECT COUNT(*) FROM pragma_table_info('{table}') WHERE name=?", (col,)
            ).fetchone()[0]
            if not exists:
                conn.execute(sql)

        # Indexes on columns that may not have existed at schema creation time
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_analyses_sentiment ON analyses(sentiment);
            CREATE INDEX IF NOT EXISTS idx_analyses_stage     ON analyses(relationship_stage);
        """)


# ── Chat CRUD ────────────────────────────────────────────────────────────────

def upsert_chat(chat: ParsedChat) -> int:
    """
    Insert or replace a chat record. Returns the chat_id.
    Idempotent — re-uploading the same filename replaces the record.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM chats WHERE filename = ?", (chat.filename,)
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM messages        WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM financial_mentions WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM concrete_orders WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM action_items    WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM contacts        WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM projects        WHERE chat_id = ?", (existing['id'],))
            conn.execute("DELETE FROM analyses        WHERE chat_id = ?", (existing['id'],))

        conn.execute("""
            INSERT OR REPLACE INTO chats
                (filename, chat_name, imported_at, raw_text,
                 message_count, date_first_msg, date_last_msg, platform)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat.filename,
            chat.chat_name,
            now,
            chat.raw_text,
            chat.message_count,
            chat.date_first_msg,
            chat.date_last_msg,
            chat.platform,
        ))
        row = conn.execute(
            "SELECT id FROM chats WHERE filename = ?", (chat.filename,)
        ).fetchone()
        return row['id']


def insert_messages(chat_id: int, chat: 'ParsedChat') -> None:
    """Bulk-insert all messages for a chat."""
    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO messages
                (chat_id, timestamp, sender, body, is_media, is_voice_note, attached_filename, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                chat_id,
                m.timestamp,
                m.sender,
                m.body,
                int(m.is_media),
                int(m.is_voice_note),
                m.attached_filename,
                m.seq,
            )
            for m in chat.messages
        ])


def get_media_dir(chat_id: int) -> str:
    """Return (and create) the media storage directory for a chat."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'data', 'media', str(chat_id)
    )
    os.makedirs(path, exist_ok=True)
    return path


def copy_media_files(chat_id: int, source_folder: str) -> Dict[str, str]:
    """
    Copy all media files from a WhatsApp export folder to data/media/{chat_id}/.
    Returns a dict mapping original filename → local media_path.
    """
    media_dir = get_media_dir(chat_id)
    copied: Dict[str, str] = {}
    try:
        for fname in os.listdir(source_folder):
            if fname.startswith('_') or fname.startswith('.') or fname == '_chat.txt':
                continue
            src = os.path.join(source_folder, fname)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(media_dir, fname)
            shutil.copy2(src, dst)
            copied[fname] = dst
    except (PermissionError, OSError):
        pass

    if copied:
        with get_connection() as conn:
            for fname, dst in copied.items():
                conn.execute(
                    "UPDATE messages SET media_path=? WHERE chat_id=? AND attached_filename=?",
                    (dst, chat_id, fname),
                )
    return copied


def save_transcription(
    message_id: int,
    transcription: str,
    translation: Optional[str],
    summary: Optional[str] = None,
    location: Optional[str] = None,
) -> None:
    """Store transcription, translation, summary, and detected location for a voice note."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE messages SET transcription=?, translation=?, vn_summary=?, vn_location=? WHERE id=?",
            (transcription, translation, summary, location, message_id),
        )


def get_voice_notes(chat_id: int) -> List[sqlite3.Row]:
    """Return all voice note messages for a chat."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM messages WHERE chat_id=? AND is_voice_note=1 ORDER BY seq",
            (chat_id,)
        ).fetchall()


def get_all_chats() -> List[sqlite3.Row]:
    """Return all chats joined with their analysis (LEFT JOIN)."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.*, a.primary_area, a.category, a.status, a.urgency_level,
                   a.sentiment, a.relationship_stage,
                   a.executive_summary, a.followup_needed, a.last_activity_date,
                   CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER)
                       AS days_silent,
                   ct.name AS contact_name, ct.role AS contact_role, ct.company,
                   p.type AS project_type, p.total_m3_estimate
            FROM chats c
            LEFT JOIN analyses a ON a.chat_id = c.id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            LEFT JOIN projects p  ON p.chat_id  = c.id
            ORDER BY c.imported_at DESC
        """).fetchall()


def get_chat_by_id(chat_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()


def get_chat_by_filename(filename: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM chats WHERE filename = ?", (filename,)
        ).fetchone()


def get_messages(chat_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY seq",
            (chat_id,)
        ).fetchall()


# ── Analysis CRUD ────────────────────────────────────────────────────────────

def save_analysis(chat_id: int, data: Dict[str, Any]) -> None:
    """
    Upsert an analysis record from the Claude response dict.
    Uses INSERT OR REPLACE (chat_id is UNIQUE).
    """
    now = datetime.now(timezone.utc).isoformat()
    payment = data.get('payment_info') or {}
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO analyses (
                chat_id, analyzed_at, model_used,
                primary_area, secondary_areas, category, status, urgency_level,
                sentiment, relationship_stage, language_mix,
                executive_summary, timeline_json,
                followup_needed, followup_reason, followup_action,
                negotiation_signals, last_activity_date, lifecycle_transitions,
                competitors_mentioned,
                payment_terms, payment_method, payment_outstanding, payment_overdue,
                raw_claude_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            now,
            'claude-haiku-4-5-20251001',
            data.get('primary_area'),
            json.dumps(data.get('secondary_areas', [])),
            data.get('category'),
            data.get('status'),
            data.get('urgency_level'),
            data.get('sentiment'),
            data.get('relationship_stage'),
            json.dumps(data.get('language_mix', [])),
            data.get('executive_summary'),
            json.dumps(data.get('timeline', [])),
            int(bool(data.get('followup_needed', False))),
            data.get('followup_reason'),
            data.get('followup_action'),
            json.dumps(data.get('negotiation_signals', [])),
            data.get('last_activity_date'),
            json.dumps(data.get('lifecycle_transitions', [])),
            json.dumps(data.get('competitors_mentioned', [])),
            payment.get('terms'),
            payment.get('method'),
            payment.get('outstanding_amount'),
            int(bool(payment.get('overdue', False))),
            json.dumps(data),
        ))


def get_analysis(chat_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM analyses WHERE chat_id = ?", (chat_id,)
        ).fetchone()


def update_area(chat_id: int, area: str) -> None:
    """Manually override the primary_area for a chat analysis."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE analyses SET primary_area = ? WHERE chat_id = ?",
            (area, chat_id),
        )


def mark_followup_done(chat_id: int) -> None:
    """Clear the follow-up flag and set status to Active."""
    with get_connection() as conn:
        conn.execute("""
            UPDATE analyses
            SET followup_needed = 0, status = 'Active'
            WHERE chat_id = ?
        """, (chat_id,))


# ── Contact CRUD ──────────────────────────────────────────────────────────────

def save_contact_info(chat_id: int, contact: Dict[str, Any]) -> None:
    """Upsert contact record extracted from Claude analysis."""
    if not contact or not any(contact.values()):
        return
    now = datetime.now(timezone.utc).isoformat()
    role = contact.get('role') or 'Unknown'
    valid_roles = ('Contractor', 'Developer', 'Project Manager', 'Dealer',
                   'Architect', 'Engineer', 'Unknown')
    if role not in valid_roles:
        role = 'Unknown'
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO contacts
                (chat_id, name, phone, role, company, is_decision_maker, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            contact.get('name'),
            contact.get('phone'),
            role,
            contact.get('company'),
            int(bool(contact.get('is_decision_maker', False))),
            now,
        ))


def get_contact(chat_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM contacts WHERE chat_id = ?", (chat_id,)
        ).fetchone()


# ── Project CRUD ──────────────────────────────────────────────────────────────

def save_project_info(chat_id: int, project: Dict[str, Any]) -> None:
    """Upsert project record extracted from Claude analysis."""
    if not project or not any(v for v in project.values() if v is not None):
        return
    now = datetime.now(timezone.utc).isoformat()
    ptype = project.get('type') or 'Unknown'
    valid_types = ('Residential', 'Commercial', 'Infrastructure', 'Industrial', 'Unknown')
    if ptype not in valid_types:
        ptype = 'Unknown'
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO projects
                (chat_id, name, type, location_detail, floors, area_m2,
                 total_m3_estimate, start_date, completion_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            project.get('name'),
            ptype,
            project.get('location_detail'),
            project.get('floors'),
            project.get('area_m2'),
            project.get('total_m3_estimate'),
            project.get('start_date'),
            project.get('completion_date'),
            now,
        ))


def get_project(chat_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects WHERE chat_id = ?", (chat_id,)
        ).fetchone()


# ── Concrete Orders CRUD ──────────────────────────────────────────────────────

def save_concrete_orders(chat_id: int, orders: List[Dict[str, Any]]) -> None:
    """Replace all concrete orders for a chat."""
    if not orders:
        return
    valid_statuses = ('Quoted', 'Ordered', 'Delivered', 'Cancelled')
    with get_connection() as conn:
        conn.execute("DELETE FROM concrete_orders WHERE chat_id = ?", (chat_id,))
        conn.executemany("""
            INSERT INTO concrete_orders
                (chat_id, mix_grade, slump, pump_required, volume_m3,
                 price_per_m3, currency, delivery_date, status, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                chat_id,
                o.get('mix_grade'),
                str(o.get('slump')) if o.get('slump') is not None else None,
                int(bool(o.get('pump_required', False))),
                o.get('volume_m3'),
                o.get('price_per_m3'),
                o.get('currency', 'USD'),
                o.get('delivery_date'),
                o.get('status') if o.get('status') in valid_statuses else 'Quoted',
                i,
            )
            for i, o in enumerate(orders)
        ])


def get_concrete_orders(chat_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM concrete_orders WHERE chat_id = ? ORDER BY seq",
            (chat_id,)
        ).fetchall()


# ── Action Items CRUD ─────────────────────────────────────────────────────────

def save_action_items(chat_id: int, items: List[Dict[str, Any]]) -> None:
    """Replace all action items for a chat."""
    if not items:
        return
    now = datetime.now(timezone.utc).isoformat()
    valid_priorities = ('Low', 'Medium', 'High', 'Critical')
    with get_connection() as conn:
        conn.execute("DELETE FROM action_items WHERE chat_id = ?", (chat_id,))
        conn.executemany("""
            INSERT INTO action_items
                (chat_id, action, due_date, priority, completed, created_at, seq)
            VALUES (?, ?, ?, ?, 0, ?, ?)
        """, [
            (
                chat_id,
                item.get('action', ''),
                item.get('due_date'),
                item.get('priority') if item.get('priority') in valid_priorities else 'Medium',
                now,
                i,
            )
            for i, item in enumerate(items)
            if item.get('action')
        ])


def get_action_items(chat_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM action_items WHERE chat_id = ? ORDER BY seq",
            (chat_id,)
        ).fetchall()


def complete_action_item(item_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE action_items SET completed=1, completed_at=? WHERE id=?",
            (now, item_id),
        )


def get_open_action_items(
    area: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[sqlite3.Row]:
    """All incomplete action items across all chats, sorted by priority."""
    with get_connection() as conn:
        wheres = ["ai.completed = 0"]
        params: List[Any] = []
        if area:
            wheres.append("an.primary_area = ?")
            params.append(area)
        if priority:
            wheres.append("ai.priority = ?")
            params.append(priority)
        where_clause = ' AND '.join(wheres)
        return conn.execute(f"""
            SELECT ai.*, c.chat_name, c.id AS chat_id,
                   an.primary_area, an.urgency_level
            FROM action_items ai
            JOIN chats c ON c.id = ai.chat_id
            LEFT JOIN analyses an ON an.chat_id = ai.chat_id
            WHERE {where_clause}
            ORDER BY
                CASE ai.priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High'     THEN 2
                    WHEN 'Medium'   THEN 3
                    ELSE 4
                END,
                ai.due_date ASC NULLS LAST
        """, params).fetchall()


# ── Financial mentions CRUD ──────────────────────────────────────────────────

def save_financial_mentions(chat_id: int, mentions: List[Dict[str, Any]]) -> None:
    """Replace all financial mentions for a chat."""
    with get_connection() as conn:
        conn.execute("DELETE FROM financial_mentions WHERE chat_id = ?", (chat_id,))
        conn.executemany("""
            INSERT INTO financial_mentions
                (chat_id, mention_date, mention_type, amount, currency,
                 raw_text, context_note, seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                chat_id,
                m.get('mention_date'),
                m.get('mention_type', 'other'),
                m.get('amount'),
                m.get('currency', 'USD'),
                m.get('raw_text', ''),
                m.get('context_note', ''),
                i,
            )
            for i, m in enumerate(mentions)
        ])


def get_financial_mentions(chat_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM financial_mentions WHERE chat_id = ? ORDER BY seq",
            (chat_id,)
        ).fetchall()


# ── Dashboard KPIs ───────────────────────────────────────────────────────────

def get_kpis() -> Dict[str, Any]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE status = 'Active'"
        ).fetchone()[0]
        followups = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE followup_needed = 1"
        ).fetchone()[0]
        high_risk = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE urgency_level IN ('High','Critical')"
        ).fetchone()[0]
        open_actions = conn.execute(
            "SELECT COUNT(*) FROM action_items WHERE completed = 0"
        ).fetchone()[0]
        total_m3 = conn.execute(
            "SELECT COALESCE(SUM(volume_m3), 0) FROM concrete_orders "
            "WHERE status IN ('Quoted','Ordered')"
        ).fetchone()[0]
        overdue_payments = conn.execute(
            "SELECT COUNT(*) FROM analyses WHERE payment_overdue = 1"
        ).fetchone()[0]
        hot_leads = conn.execute(
            "SELECT COUNT(*) FROM analyses "
            "WHERE relationship_stage IN ('Hot','Negotiating')"
        ).fetchone()[0]
        return {
            'total_chats': total,
            'active_clients': active,
            'followups_due': followups,
            'high_risk': high_risk,
            'open_actions': open_actions,
            'pipeline_m3': round(total_m3 or 0, 1),
            'overdue_payments': overdue_payments,
            'hot_leads': hot_leads,
        }


# ── Area overview ────────────────────────────────────────────────────────────

def get_area_stats() -> List[Dict[str, Any]]:
    """Aggregate counts and pipeline value per primary_area."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                a.primary_area,
                COUNT(DISTINCT a.chat_id)   AS total_chats,
                SUM(CASE WHEN a.status = 'Active'                        THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN a.relationship_stage IN ('Hot','Negotiating') THEN 1 ELSE 0 END) AS hot,
                SUM(CASE WHEN a.category = 'Potential Client'             THEN 1 ELSE 0 END) AS leads,
                SUM(CASE WHEN a.category = 'Project'                      THEN 1 ELSE 0 END) AS projects,
                SUM(CASE WHEN a.status IN ('Closed','Lost')               THEN 1 ELSE 0 END) AS closed,
                COALESCE(SUM(co_agg.area_m3), 0)  AS pipeline_m3,
                COALESCE(SUM(fm_agg.area_value), 0) AS pipeline_usd
            FROM analyses a
            LEFT JOIN (
                SELECT co.chat_id, SUM(co.volume_m3) AS area_m3
                FROM concrete_orders co
                WHERE co.status IN ('Quoted','Ordered')
                GROUP BY co.chat_id
            ) co_agg ON co_agg.chat_id = a.chat_id
            LEFT JOIN (
                SELECT fm.chat_id, SUM(fm.amount) AS area_value
                FROM financial_mentions fm
                WHERE fm.mention_type IN ('total_order','quote','price_per_m3')
                  AND fm.currency = 'USD'
                GROUP BY fm.chat_id
            ) fm_agg ON fm_agg.chat_id = a.chat_id
            WHERE a.primary_area IS NOT NULL
            GROUP BY a.primary_area
            ORDER BY total_chats DESC
        """).fetchall()
        return [dict(r) for r in rows]


# ── Follow-ups ───────────────────────────────────────────────────────────────

def get_followups(area: Optional[str] = None,
                  categories: Optional[List[str]] = None,
                  overdue_only: bool = False) -> List[sqlite3.Row]:
    with get_connection() as conn:
        wheres = ["a.followup_needed = 1"]
        params: List[Any] = []

        if area:
            wheres.append("a.primary_area = ?")
            params.append(area)
        if categories:
            placeholders = ','.join(['?'] * len(categories))
            wheres.append(f"a.category IN ({placeholders})")
            params.extend(categories)
        if overdue_only:
            wheres.append(
                "CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER) > 7"
            )

        where_clause = ' AND '.join(wheres)
        return conn.execute(f"""
            SELECT c.id, c.chat_name, c.filename,
                   a.primary_area, a.category, a.urgency_level,
                   a.followup_action, a.followup_reason,
                   a.last_activity_date, a.status, a.relationship_stage,
                   ct.name AS contact_name, ct.role AS contact_role,
                   CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER)
                       AS days_silent
            FROM analyses a
            JOIN chats c ON c.id = a.chat_id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            WHERE {where_clause}
            ORDER BY
                CASE a.urgency_level
                    WHEN 'Critical' THEN 1
                    WHEN 'High'     THEN 2
                    WHEN 'Medium'   THEN 3
                    ELSE 4
                END,
                a.last_activity_date ASC
        """, params).fetchall()


# ── Risk flags ───────────────────────────────────────────────────────────────

def get_silent_high_value_leads() -> List[sqlite3.Row]:
    """Potential Leads silent > 14 days that have financial data."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.id, c.chat_name,
                   a.primary_area, a.urgency_level, a.last_activity_date,
                   a.relationship_stage,
                   CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER)
                       AS days_silent,
                   ct.name AS contact_name, ct.role AS contact_role,
                   (SELECT SUM(co.volume_m3)
                    FROM concrete_orders co
                    WHERE co.chat_id = c.id) AS total_m3,
                   (SELECT SUM(fm.amount)
                    FROM financial_mentions fm
                    WHERE fm.chat_id = c.id AND fm.currency = 'USD') AS total_value
            FROM analyses a
            JOIN chats c ON c.id = a.chat_id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            WHERE a.category = 'Potential Client'
              AND CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER) > 14
              AND EXISTS (
                  SELECT 1 FROM financial_mentions fm WHERE fm.chat_id = c.id
              )
            ORDER BY days_silent DESC
        """).fetchall()


def get_stalled_negotiations() -> List[sqlite3.Row]:
    """Waiting/Negotiating status, silent > 7 days."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.id, c.chat_name,
                   a.primary_area, a.urgency_level, a.last_activity_date,
                   a.negotiation_signals, a.relationship_stage,
                   ct.name AS contact_name,
                   CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER)
                       AS days_silent
            FROM analyses a
            JOIN chats c ON c.id = a.chat_id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            WHERE (a.status = 'Waiting' OR a.relationship_stage = 'Negotiating')
              AND a.negotiation_signals IS NOT NULL
              AND a.negotiation_signals != '[]'
              AND CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER) > 7
            ORDER BY days_silent DESC
        """).fetchall()


def get_lifecycle_stuck() -> List[sqlite3.Row]:
    """Silent > 30 days."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.id, c.chat_name,
                   a.primary_area, a.status, a.category, a.relationship_stage,
                   a.last_activity_date, a.analyzed_at,
                   ct.name AS contact_name,
                   CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER)
                       AS days_silent,
                   CAST(julianday(a.analyzed_at) - julianday(a.last_activity_date) AS INTEGER)
                       AS gap_days
            FROM analyses a
            JOIN chats c ON c.id = a.chat_id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            WHERE CAST(julianday('now') - julianday(a.last_activity_date) AS INTEGER) > 30
            ORDER BY days_silent DESC
        """).fetchall()


def get_overdue_payments() -> List[sqlite3.Row]:
    """Chats flagged as having overdue payments."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.id, c.chat_name,
                   a.primary_area, a.urgency_level, a.last_activity_date,
                   a.payment_terms, a.payment_outstanding,
                   ct.name AS contact_name, ct.company
            FROM analyses a
            JOIN chats c ON c.id = a.chat_id
            LEFT JOIN contacts ct ON ct.chat_id = c.id
            WHERE a.payment_overdue = 1
            ORDER BY a.payment_outstanding DESC NULLS LAST
        """).fetchall()


# ── Pipeline aggregations ─────────────────────────────────────────────────────

def get_pipeline_summary() -> Dict[str, Any]:
    """Cross-chat pipeline totals for the dashboard."""
    with get_connection() as conn:
        m3_row = conn.execute("""
            SELECT
                SUM(CASE WHEN status = 'Quoted'    THEN volume_m3 ELSE 0 END) AS quoted_m3,
                SUM(CASE WHEN status = 'Ordered'   THEN volume_m3 ELSE 0 END) AS ordered_m3,
                SUM(CASE WHEN status = 'Delivered' THEN volume_m3 ELSE 0 END) AS delivered_m3
            FROM concrete_orders
        """).fetchone()
        mix_rows = conn.execute("""
            SELECT mix_grade, SUM(volume_m3) AS total_m3, COUNT(*) AS order_count
            FROM concrete_orders
            WHERE mix_grade IS NOT NULL AND status IN ('Quoted','Ordered')
            GROUP BY mix_grade ORDER BY total_m3 DESC
        """).fetchall()
        area_rows = conn.execute("""
            SELECT an.primary_area, SUM(co.volume_m3) AS m3
            FROM concrete_orders co
            JOIN analyses an ON an.chat_id = co.chat_id
            WHERE co.status IN ('Quoted','Ordered') AND an.primary_area IS NOT NULL
            GROUP BY an.primary_area ORDER BY m3 DESC LIMIT 10
        """).fetchall()
        return {
            'quoted_m3':   round(m3_row['quoted_m3']    or 0, 1),
            'ordered_m3':  round(m3_row['ordered_m3']   or 0, 1),
            'delivered_m3':round(m3_row['delivered_m3'] or 0, 1),
            'by_mix':  [dict(r) for r in mix_rows],
            'by_area': [dict(r) for r in area_rows],
        }


def get_contacts_by_area(area: Optional[str] = None) -> List[sqlite3.Row]:
    """List all contacts with their analysis data, optionally filtered by area."""
    with get_connection() as conn:
        where = "WHERE an.primary_area = ?" if area else ""
        params = (area,) if area else ()
        return conn.execute(f"""
            SELECT ct.*, c.chat_name, c.id AS chat_id,
                   an.primary_area, an.status, an.urgency_level,
                   an.relationship_stage, an.last_activity_date
            FROM contacts ct
            JOIN chats c ON c.id = ct.chat_id
            LEFT JOIN analyses an ON an.chat_id = ct.chat_id
            {where}
            ORDER BY an.relationship_stage, ct.name
        """, params).fetchall()


# ── Utility ───────────────────────────────────────────────────────────────────

def get_distinct_areas() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT primary_area FROM analyses "
            "WHERE primary_area IS NOT NULL ORDER BY primary_area"
        ).fetchall()
        return [r[0] for r in rows]


def get_distinct_categories() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM analyses "
            "WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
        return [r[0] for r in rows]
