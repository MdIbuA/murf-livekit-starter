import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("db")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kisan_mitra.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database and creates the farmers table if missing."""
    conn = get_connection()
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

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
