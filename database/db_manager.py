"""
Database Manager for persistent storage using SQLite.
Stores active giveaways, user warnings, channel overrides, and prepares schemas
for future shop, economy, license key, and inventory modules.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "bot_data.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables for giveaways, warnings, and future shop extensions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # --- Giveaways Table ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    message_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    prize TEXT NOT NULL,
                    host_id INTEGER NOT NULL,
                    winner_count INTEGER NOT NULL,
                    end_time REAL NOT NULL,
                    forced_user_id INTEGER,
                    entries TEXT NOT NULL DEFAULT '[]',
                    ended INTEGER NOT NULL DEFAULT 0
                )
            """)

            # --- User Warnings Table ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)

            # --- Future Ready Schema Placeholders (Shop, Inventory, Licenses, Economy) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    stock_type TEXT DEFAULT 'key'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS license_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    key_code TEXT NOT NULL UNIQUE,
                    is_used INTEGER DEFAULT 0,
                    buyer_id INTEGER
                )
            """)

            conn.commit()

    # --- Giveaway Methods ---
    def save_giveaway(self, message_id: int, channel_id: int, guild_id: int, prize: str, host_id: int, winner_count: int, end_time: float, forced_user_id: Optional[int] = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO giveaways (message_id, channel_id, guild_id, prize, host_id, winner_count, end_time, forced_user_id, entries, ended)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', 0)
            """, (message_id, channel_id, guild_id, prize, host_id, winner_count, end_time, forced_user_id))
            conn.commit()

    def get_giveaway(self, message_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM giveaways WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['entries'] = json.loads(data['entries'])
                return data
            return None

    def get_active_giveaways(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM giveaways WHERE ended = 0")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                data = dict(row)
                data['entries'] = json.loads(data['entries'])
                results.append(data)
            return results

    def add_giveaway_entry(self, message_id: int, user_id: int) -> bool:
        """Add user to giveaway entries. Returns True if added, False if already entered."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entries FROM giveaways WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            if not row:
                return False
            entries = json.loads(row['entries'])
            if user_id in entries:
                return False
            entries.append(user_id)
            cursor.execute("UPDATE giveaways SET entries = ? WHERE message_id = ?", (json.dumps(entries), message_id))
            conn.commit()
            return True

    def remove_giveaway_entry(self, message_id: int, user_id: int) -> bool:
        """Remove user from giveaway entries. Returns True if removed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entries FROM giveaways WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()
            if not row:
                return False
            entries = json.loads(row['entries'])
            if user_id not in entries:
                return False
            entries.remove(user_id)
            cursor.execute("UPDATE giveaways SET entries = ? WHERE message_id = ?", (json.dumps(entries), message_id))
            conn.commit()
            return True

    def end_giveaway(self, message_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE giveaways SET ended = 1 WHERE message_id = ?", (message_id,))
            conn.commit()

    def delete_giveaway(self, message_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM giveaways WHERE message_id = ?", (message_id,))
            conn.commit()

    # --- Warning Methods ---
    def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str, timestamp: float):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, reason, timestamp))
            conn.commit()

    def get_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC
            """, (guild_id, user_id))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def clear_warnings(self, guild_id: int, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            conn.commit()


# Global database instance
db = DatabaseManager()
