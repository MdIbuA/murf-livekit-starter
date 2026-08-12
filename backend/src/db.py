import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger("db")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kisan_mitra.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database and creates all tables if missing."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Farmers table (Day 4) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT DEFAULT 'Hinglish',
            district TEXT,
            crops_grown TEXT,
            land_size TEXT,
            irrigation_type TEXT,
            last_topic TEXT,
            last_interaction TIMESTAMP
        )
    """)

    # --- Escalations table (Day 7) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE NOT NULL,
            farmer_id TEXT,
            farmer_name TEXT,
            trigger_type TEXT NOT NULL,
            situation_summary TEXT NOT NULL,
            already_checked TEXT,
            urgency TEXT DEFAULT 'medium',
            language TEXT DEFAULT 'Tamil',
            contact_method TEXT DEFAULT 'phone',
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


# ---------------------------------------------------------------------------
# Farmers CRUD (Day 4)
# ---------------------------------------------------------------------------

def get_farmer(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a farmer's profile by user_id."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM farmers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def save_farmer(
    user_id: str,
    name: Optional[str] = None,
    language_preference: Optional[str] = "Hinglish",
    district: Optional[str] = None,
    crops_grown: Optional[str] = None,
    land_size: Optional[str] = None,
    irrigation_type: Optional[str] = None,
    last_topic: Optional[str] = None
) -> Dict[str, Any]:
    """Inserts or updates a farmer profile in the database."""
    init_db()
    existing = get_farmer(user_id)
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    if existing:
        # Update fields if provided, otherwise preserve existing values
        updated_name = name if name is not None else existing.get("name")
        updated_lang = language_preference if language_preference is not None else existing.get("language_preference")
        updated_district = district if district is not None else existing.get("district")
        updated_crops = crops_grown if crops_grown is not None else existing.get("crops_grown")
        updated_land = land_size if land_size is not None else existing.get("land_size")
        updated_irrigation = irrigation_type if irrigation_type is not None else existing.get("irrigation_type")
        updated_topic = last_topic if last_topic is not None else existing.get("last_topic")

        cursor.execute("""
            UPDATE farmers SET
                name = ?,
                language_preference = ?,
                district = ?,
                crops_grown = ?,
                land_size = ?,
                irrigation_type = ?,
                last_topic = ?,
                last_interaction = ?
            WHERE user_id = ?
        """, (updated_name, updated_lang, updated_district, updated_crops, updated_land, updated_irrigation, updated_topic, now, user_id))
    else:
        cursor.execute("""
            INSERT INTO farmers (user_id, name, language_preference, district, crops_grown, land_size, irrigation_type, last_topic, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, language_preference, district, crops_grown, land_size, irrigation_type, last_topic, now))

    conn.commit()
    conn.close()
    logger.info(f"Saved farmer profile for user_id={user_id}")
    return get_farmer(user_id) or {}

def delete_farmer(user_id: str) -> bool:
    """Deletes a farmer's profile from the database (Forget Me tool)."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM farmers WHERE user_id = ?", (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    logger.info(f"Deleted farmer profile for user_id={user_id}: {deleted}")
    return deleted


# ---------------------------------------------------------------------------
# Escalations CRUD (Day 7)
# ---------------------------------------------------------------------------

def _generate_reference_id(cursor) -> str:
    """Auto-generate a KM-YYYYMMDD-XXXX reference ID using today's date + daily counter."""
    today_str = datetime.now().strftime("%Y%m%d")
    prefix = f"KM-{today_str}-"
    cursor.execute(
        "SELECT COUNT(*) FROM escalations WHERE reference_id LIKE ?",
        (prefix + "%",)
    )
    count = cursor.fetchone()[0]
    return f"{prefix}{str(count + 1).zfill(4)}"


def create_escalation_record(
    farmer_id: str,
    farmer_name: str,
    trigger_type: str,
    situation_summary: str,
    already_checked: str = "",
    urgency: str = "medium",
    language: str = "Tamil",
    contact_method: str = "phone",
) -> Dict[str, Any]:
    """
    Creates a new escalation record in the database.

    Args:
        farmer_id: Caller / user ID of the farmer
        farmer_name: Farmer's display name (may be 'Unknown')
        trigger_type: 'crop_emergency' or 'market_data_missing' (or free text)
        situation_summary: Concise human-readable summary (PII already scrubbed by caller)
        already_checked: What the agent already tried (e.g. 'Checked paddy price tool — no data returned')
        urgency: 'low' | 'medium' | 'high' | 'emergency'
        language: Language of the caller (e.g. 'Tamil', 'Tamil+English')
        contact_method: How the farmer prefers to be reached ('phone', 'whatsapp', 'none')
    Returns:
        The created escalation record as a dict (includes reference_id).
    """
    init_db()
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    reference_id = _generate_reference_id(cursor)

    cursor.execute("""
        INSERT INTO escalations
            (reference_id, farmer_id, farmer_name, trigger_type,
             situation_summary, already_checked, urgency, language,
             contact_method, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (
        reference_id, farmer_id, farmer_name, trigger_type,
        situation_summary, already_checked, urgency, language,
        contact_method, now, now
    ))

    conn.commit()
    conn.close()

    logger.info(f"Created escalation {reference_id} for farmer_id={farmer_id} trigger={trigger_type} urgency={urgency}")
    return get_escalation(reference_id) or {}


def get_escalation(reference_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single escalation record by reference_id."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM escalations WHERE reference_id = ?", (reference_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_escalations(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all escalation records, newest first.
    Optionally filter by status: 'open' | 'in_progress' | 'resolved'
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM escalations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_escalation_status(reference_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    """
    Updates the status of an escalation.
    Valid statuses: 'open', 'in_progress', 'resolved'
    Returns the updated record, or None if not found.
    """
    valid = {"open", "in_progress", "resolved"}
    if new_status not in valid:
        raise ValueError(f"Invalid status '{new_status}'. Must be one of {valid}")

    init_db()
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE escalations SET status = ?, updated_at = ? WHERE reference_id = ?",
        (new_status, now, reference_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if updated:
        logger.info(f"Escalation {reference_id} status → {new_status}")
        return get_escalation(reference_id)
    logger.warning(f"Escalation {reference_id} not found for status update")
    return None
