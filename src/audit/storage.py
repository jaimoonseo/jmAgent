"""Storage backend for audit logs using SQLite."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class AuditQuery:
    """Query filter for audit log retrieval."""

    action_type: Optional[str] = None
    user: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditStorage:
    """
    Storage backend for audit logs using SQLite.

    Provides persistence and querying capabilities for audit records.
    """

    def __init__(self, db_path: str = "audit.db"):
        """
        Initialize AuditStorage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database schema if not already done."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                user TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                input_data TEXT NOT NULL,
                output_data TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                duration REAL,
                tokens_used TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_type
            ON audit_logs(action_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user
            ON audit_logs(user)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON audit_logs(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON audit_logs(timestamp)
        """)

        conn.commit()
        conn.close()

    def save(self, record: "AuditRecord") -> None:
        """
        Save an audit record to the database.

        Args:
            record: AuditRecord to save
        """
        # Import here to avoid circular dependency
        from src.audit.logger import AuditRecord

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO audit_logs (
                action_type, user, timestamp, input_data, output_data,
                status, error_message, duration, tokens_used, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.action_type,
            record.user,
            record.timestamp,
            json.dumps(record.input_data),
            json.dumps(record.output_data) if record.output_data else None,
            record.status,
            record.error_message,
            record.duration,
            json.dumps(record.tokens_used) if record.tokens_used else None,
            json.dumps(record.metadata) if record.metadata else None
        ))

        conn.commit()
        conn.close()

    def get_all(self) -> List["AuditRecord"]:
        """
        Retrieve all audit records.

        Returns:
            List of AuditRecord objects
        """
        from src.audit.logger import AuditRecord

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT action_type, user, timestamp, input_data, output_data,
                   status, error_message, duration, tokens_used, metadata
            FROM audit_logs
            ORDER BY timestamp DESC
        """)

        records = []
        for row in cursor.fetchall():
            record = AuditRecord(
                action_type=row[0],
                user=row[1],
                timestamp=row[2],
                input_data=json.loads(row[3]) if row[3] else {},
                output_data=json.loads(row[4]) if row[4] else None,
                status=row[5],
                error_message=row[6],
                duration=row[7],
                tokens_used=json.loads(row[8]) if row[8] else {},
                metadata=json.loads(row[9]) if row[9] else {}
            )
            records.append(record)

        conn.close()
        return records

    def query(self, query: AuditQuery) -> List["AuditRecord"]:
        """
        Query audit records with optional filters.

        Args:
            query: AuditQuery with filter criteria

        Returns:
            List of matching AuditRecord objects
        """
        from src.audit.logger import AuditRecord

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sql = """
            SELECT action_type, user, timestamp, input_data, output_data,
                   status, error_message, duration, tokens_used, metadata
            FROM audit_logs
            WHERE 1=1
        """
        params = []

        if query.action_type:
            sql += " AND action_type = ?"
            params.append(query.action_type)

        if query.user:
            sql += " AND user = ?"
            params.append(query.user)

        if query.status:
            sql += " AND status = ?"
            params.append(query.status)

        if query.start_date:
            start_iso = query.start_date.isoformat().replace("+00:00", "Z")
            sql += " AND timestamp >= ?"
            params.append(start_iso)

        if query.end_date:
            end_iso = query.end_date.isoformat().replace("+00:00", "Z")
            sql += " AND timestamp <= ?"
            params.append(end_iso)

        sql += " ORDER BY timestamp DESC"

        cursor.execute(sql, params)

        records = []
        for row in cursor.fetchall():
            record = AuditRecord(
                action_type=row[0],
                user=row[1],
                timestamp=row[2],
                input_data=json.loads(row[3]) if row[3] else {},
                output_data=json.loads(row[4]) if row[4] else None,
                status=row[5],
                error_message=row[6],
                duration=row[7],
                tokens_used=json.loads(row[8]) if row[8] else {},
                metadata=json.loads(row[9]) if row[9] else {}
            )
            records.append(record)

        conn.close()
        return records

    def get_count_by_action(self) -> Dict[str, int]:
        """
        Get count of records grouped by action type.

        Returns:
            Dictionary with action types as keys and counts as values
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM audit_logs
            GROUP BY action_type
        """)

        counts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return counts

    def get_count_by_user(self) -> Dict[str, int]:
        """
        Get count of records grouped by user.

        Returns:
            Dictionary with usernames as keys and counts as values
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user, COUNT(*) as count
            FROM audit_logs
            GROUP BY user
        """)

        counts = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return counts

    def delete_before(self, cutoff_date: datetime) -> int:
        """
        Delete audit records older than a specified date.

        Args:
            cutoff_date: Records before this date will be deleted

        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_iso = cutoff_date.isoformat().replace("+00:00", "Z")

        cursor.execute("""
            DELETE FROM audit_logs
            WHERE timestamp < ?
        """, (cutoff_iso,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def clear(self) -> None:
        """
        Clear all audit records.

        Deletes all records from the audit_logs table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM audit_logs")

        conn.commit()
        conn.close()
