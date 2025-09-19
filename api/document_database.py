"""
Document Management Database Layer
Handles document storage, metadata, and indexing status tracking.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentRecord:
    """Document metadata record."""
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_time: str
    processing_status: str  # 'pending', 'processing', 'completed', 'failed'
    processing_error: Optional[str]
    content_preview: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    is_indexed: bool
    tags: List[str]
    metadata: Dict[str, Any]


class DocumentDatabase:
    """Document management database operations."""

    def __init__(self, db_path: str = "documents.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the document database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TEXT NOT NULL,
                    processing_status TEXT NOT NULL DEFAULT 'pending',
                    processing_error TEXT,
                    content_preview TEXT,
                    page_count INTEGER,
                    word_count INTEGER,
                    is_indexed BOOLEAN NOT NULL DEFAULT 0,
                    tags TEXT,  -- JSON array
                    metadata TEXT  -- JSON object
                )
            """)

            # Document chunks table for RAG
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    start_char INTEGER,
                    end_char INTEGER,
                    embedding_status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)

            # Document-Research session associations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_document_usage (
                    id TEXT PRIMARY KEY,
                    research_session_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    chunks_used INTEGER NOT NULL DEFAULT 0,
                    relevance_score REAL,
                    usage_time TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)

            conn.commit()

    def create_document(self, filename: str, original_name: str, file_type: str,
                       file_size: int, tags: List[str] = None,
                       metadata: Dict[str, Any] = None) -> str:
        """Create a new document record."""
        doc_id = str(uuid.uuid4())
        upload_time = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO documents (
                    id, filename, original_name, file_type, file_size,
                    upload_time, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, filename, original_name, file_type, file_size,
                upload_time, json.dumps(tags or []), json.dumps(metadata or {})
            ))
            conn.commit()

        return doc_id

    def update_processing_status(self, doc_id: str, status: str,
                               error: str = None, content_preview: str = None,
                               page_count: int = None, word_count: int = None):
        """Update document processing status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents
                SET processing_status = ?, processing_error = ?,
                    content_preview = ?, page_count = ?, word_count = ?
                WHERE id = ?
            """, (status, error, content_preview, page_count, word_count, doc_id))
            conn.commit()

    def mark_as_indexed(self, doc_id: str):
        """Mark document as successfully indexed for RAG."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents SET is_indexed = 1 WHERE id = ?
            """, (doc_id,))
            conn.commit()

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        """Get document by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,))
            row = cursor.fetchone()

            if row:
                return DocumentRecord(
                    id=row['id'],
                    filename=row['filename'],
                    original_name=row['original_name'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    upload_time=row['upload_time'],
                    processing_status=row['processing_status'],
                    processing_error=row['processing_error'],
                    content_preview=row['content_preview'],
                    page_count=row['page_count'],
                    word_count=row['word_count'],
                    is_indexed=bool(row['is_indexed']),
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
        return None

    def get_all_documents(self, status_filter: str = None) -> List[DocumentRecord]:
        """Get all documents, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if status_filter:
                cursor = conn.execute("""
                    SELECT * FROM documents WHERE processing_status = ?
                    ORDER BY upload_time DESC
                """, (status_filter,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM documents ORDER BY upload_time DESC
                """)

            rows = cursor.fetchall()
            return [
                DocumentRecord(
                    id=row['id'],
                    filename=row['filename'],
                    original_name=row['original_name'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    upload_time=row['upload_time'],
                    processing_status=row['processing_status'],
                    processing_error=row['processing_error'],
                    content_preview=row['content_preview'],
                    page_count=row['page_count'],
                    word_count=row['word_count'],
                    is_indexed=bool(row['is_indexed']),
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                for row in rows
            ]

    def get_indexed_documents(self) -> List[DocumentRecord]:
        """Get all documents that are successfully indexed."""
        return self.get_all_documents(status_filter='completed')

    def delete_document(self, doc_id: str) -> bool:
        """Delete document and all associated data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_document_chunk(self, document_id: str, chunk_index: int, content: str,
                          page_number: int = None, start_char: int = None,
                          end_char: int = None) -> str:
        """Add a document chunk for RAG processing."""
        chunk_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO document_chunks (
                    id, document_id, chunk_index, content, page_number,
                    start_char, end_char, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (chunk_id, document_id, chunk_index, content, page_number,
                  start_char, end_char, created_at))
            conn.commit()

        return chunk_id

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM document_chunks
                WHERE document_id = ?
                ORDER BY chunk_index
            """, (document_id,))

            return [dict(row) for row in cursor.fetchall()]

    def record_document_usage(self, research_session_id: str, document_id: str,
                            chunks_used: int = 0, relevance_score: float = None):
        """Record that a document was used in a research session."""
        usage_id = str(uuid.uuid4())
        usage_time = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO research_document_usage (
                    id, research_session_id, document_id, chunks_used,
                    relevance_score, usage_time
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (usage_id, research_session_id, document_id, chunks_used,
                  relevance_score, usage_time))
            conn.commit()

    def get_document_stats(self) -> Dict[str, Any]:
        """Get document collection statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_documents,
                    COUNT(CASE WHEN is_indexed = 1 THEN 1 END) as indexed_documents,
                    COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed_documents,
                    SUM(file_size) as total_size_bytes
                FROM documents
            """)

            stats = dict(cursor.fetchone())

            # Get file type distribution
            cursor = conn.execute("""
                SELECT file_type, COUNT(*) as count
                FROM documents
                GROUP BY file_type
            """)

            stats['file_types'] = dict(cursor.fetchall())

            return stats