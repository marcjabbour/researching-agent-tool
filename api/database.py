import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ResearchSessionRecord:
    id: str
    query: str
    depth: str
    intent: str
    status: str
    research_plan: Optional[str]  # JSON string
    execution_log: Optional[str]  # JSON string
    final_response: Optional[str]
    sources: Optional[str]  # JSON string
    created_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]

class ResearchDatabase:
    def __init__(self, db_path: str = "research_sessions.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    depth TEXT NOT NULL DEFAULT 'standard',
                    intent TEXT,
                    status TEXT NOT NULL DEFAULT 'started',
                    research_plan TEXT,  -- JSON string
                    execution_log TEXT,  -- JSON string
                    final_response TEXT,
                    sources TEXT,  -- JSON string
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds INTEGER
                )
            """)

            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON research_sessions(created_at DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON research_sessions(status)
            """)

    def create_session(self, query: str, depth: str = "standard") -> str:
        """Create a new research session"""
        session_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO research_sessions
                (id, query, depth, status, created_at)
                VALUES (?, ?, ?, 'started', ?)
            """, (session_id, query, depth, created_at))

        return session_id

    def update_session(self, session_id: str, **kwargs):
        """Update a research session with new data"""
        if not kwargs:
            return

        # Convert dict/list fields to JSON strings
        json_fields = ['research_plan', 'execution_log', 'sources']
        for field in json_fields:
            if field in kwargs and kwargs[field] is not None:
                kwargs[field] = json.dumps(kwargs[field])

        # Build dynamic UPDATE query
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [session_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE research_sessions
                SET {set_clause}
                WHERE id = ?
            """, values)

    def complete_session(self, session_id: str, final_response: str, sources: List[Dict] = None):
        """Mark a session as completed"""
        completed_at = datetime.now().isoformat()

        # Calculate duration
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT created_at FROM research_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                created_at = datetime.fromisoformat(row[0])
                completed_at_dt = datetime.fromisoformat(completed_at)
                duration = int((completed_at_dt - created_at).total_seconds())
            else:
                duration = None

        update_data = {
            'status': 'completed',
            'final_response': final_response,
            'completed_at': completed_at,
            'duration_seconds': duration
        }

        if sources:
            update_data['sources'] = sources

        self.update_session(session_id, **update_data)

    def get_session(self, session_id: str) -> Optional[ResearchSessionRecord]:
        """Get a specific research session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM research_sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()

            if row:
                return ResearchSessionRecord(
                    id=row['id'],
                    query=row['query'],
                    depth=row['depth'],
                    intent=row['intent'],
                    status=row['status'],
                    research_plan=row['research_plan'],
                    execution_log=row['execution_log'],
                    final_response=row['final_response'],
                    sources=row['sources'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    duration_seconds=row['duration_seconds']
                )
        return None

    def get_recent_sessions(self, limit: int = 50) -> List[ResearchSessionRecord]:
        """Get recent research sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM research_sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append(ResearchSessionRecord(
                    id=row['id'],
                    query=row['query'],
                    depth=row['depth'],
                    intent=row['intent'],
                    status=row['status'],
                    research_plan=row['research_plan'],
                    execution_log=row['execution_log'],
                    final_response=row['final_response'],
                    sources=row['sources'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    duration_seconds=row['duration_seconds']
                ))

            return sessions

    def get_sessions_by_status(self, status: str) -> List[ResearchSessionRecord]:
        """Get sessions by status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM research_sessions
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append(ResearchSessionRecord(
                    id=row['id'],
                    query=row['query'],
                    depth=row['depth'],
                    intent=row['intent'],
                    status=row['status'],
                    research_plan=row['research_plan'],
                    execution_log=row['execution_log'],
                    final_response=row['final_response'],
                    sources=row['sources'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    duration_seconds=row['duration_seconds']
                ))

            return sessions

    def search_sessions(self, search_term: str, limit: int = 20) -> List[ResearchSessionRecord]:
        """Search sessions by query or response content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM research_sessions
                WHERE query LIKE ? OR final_response LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f"%{search_term}%", f"%{search_term}%", limit))

            sessions = []
            for row in cursor.fetchall():
                sessions.append(ResearchSessionRecord(
                    id=row['id'],
                    query=row['query'],
                    depth=row['depth'],
                    intent=row['intent'],
                    status=row['status'],
                    research_plan=row['research_plan'],
                    execution_log=row['execution_log'],
                    final_response=row['final_response'],
                    sources=row['sources'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    duration_seconds=row['duration_seconds']
                ))

            return sessions

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_sessions,
                    AVG(CASE WHEN duration_seconds IS NOT NULL THEN duration_seconds END) as avg_duration,
                    COUNT(CASE WHEN created_at >= datetime('now', '-24 hours') THEN 1 END) as last_24h
                FROM research_sessions
            """)

            row = cursor.fetchone()
            return {
                'total_sessions': row[0],
                'completed_sessions': row[1],
                'failed_sessions': row[2],
                'average_duration_seconds': round(row[3] or 0, 2),
                'sessions_last_24h': row[4]
            }