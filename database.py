"""
Database module for parking management system.
Handles SQLite database operations for configuration and event logging.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading

class Database:
    def __init__(self, db_path: str = "parking.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _get_connection(self):
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Create database tables if they don't exist."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Events table (entry/exit log)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    vehicle_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_count INTEGER
                )
            ''')
            
            # Initialize default config if not exists
            cursor.execute("SELECT value FROM config WHERE key = 'max_capacity'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO config (key, value) VALUES ('max_capacity', '100')"
                )
            
            conn.commit()
            conn.close()
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row['value'] if row else None
    
    def set_config(self, key: str, value: str):
        """Set a configuration value."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT OR REPLACE INTO config (key, value, updated_at) 
                   VALUES (?, ?, CURRENT_TIMESTAMP)''',
                (key, value)
            )
            conn.commit()
            conn.close()
    
    def get_max_capacity(self) -> int:
        """Get the maximum parking capacity."""
        value = self.get_config('max_capacity')
        return int(value) if value else 100
    
    def set_max_capacity(self, capacity: int):
        """Set the maximum parking capacity."""
        self.set_config('max_capacity', str(capacity))
    
    def log_event(self, event_type: str, vehicle_id: int, current_count: int):
        """Log an entry or exit event."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO events (event_type, vehicle_id, current_count) 
                   VALUES (?, ?, ?)''',
                (event_type, vehicle_id, current_count)
            )
            conn.commit()
            conn.close()
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent events."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM events 
                   ORDER BY timestamp DESC 
                   LIMIT ?''',
                (limit,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
    
    def get_stats_today(self) -> Dict:
        """Get statistics for today."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Count entries and exits today
            cursor.execute(
                '''SELECT event_type, COUNT(*) as count 
                   FROM events 
                   WHERE DATE(timestamp) = DATE('now')
                   GROUP BY event_type'''
            )
            rows = cursor.fetchall()
            
            stats = {'entries': 0, 'exits': 0}
            for row in rows:
                if row['event_type'] == 'entry':
                    stats['entries'] = row['count']
                elif row['event_type'] == 'exit':
                    stats['exits'] = row['count']
            
            conn.close()
            return stats
