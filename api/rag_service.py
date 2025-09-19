"""
RAG (Retrieval-Augmented Generation) Service
Handles document indexing, similarity search, and context retrieval.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import sqlite3
from datetime import datetime
import logging

# Vector/embedding libraries
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .document_database import DocumentDatabase

logger = logging.getLogger(__name__)


@dataclass
class DocumentMatch:
    """A document chunk that matches a query."""
    document_id: str
    chunk_id: str
    content: str
    similarity_score: float
    chunk_index: int
    page_number: Optional[int] = None
    document_title: str = ""
    document_type: str = ""


@dataclass
class RAGResult:
    """Result from RAG query."""
    query: str
    matches: List[DocumentMatch]
    total_documents_searched: int
    context_used: str
    search_time: float


class RAGService:
    """Service for document retrieval and context generation."""

    def __init__(self, db_path: str = "documents.db", model_name: str = "all-MiniLM-L6-v2"):
        self.doc_db = DocumentDatabase(db_path)
        self.model_name = model_name
        self.model = None
        self.embeddings_db_path = db_path.replace(".db", "_embeddings.db")

        # Initialize embeddings database
        self._init_embeddings_db()

        # Load embedding model if available
        self._load_embedding_model()

    def _init_embeddings_db(self):
        """Initialize the embeddings database."""
        with sqlite3.connect(self.embeddings_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    model_name TEXT NOT NULL
                )
            """)
            conn.commit()

    def _load_embedding_model(self):
        """Load the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available. RAG functionality limited.")
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")

    def index_document(self, document_id: str) -> bool:
        """Index a document for RAG by creating embeddings for its chunks."""
        if not self.model:
            logger.warning("No embedding model available. Skipping indexing.")
            return False

        try:
            # Get document chunks
            chunks = self.doc_db.get_document_chunks(document_id)
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return False

            # Create embeddings for each chunk
            texts = [chunk['content'] for chunk in chunks]
            embeddings = self.model.encode(texts)

            # Store embeddings
            with sqlite3.connect(self.embeddings_db_path) as conn:
                for chunk, embedding in zip(chunks, embeddings):
                    embedding_blob = embedding.tobytes()
                    created_at = datetime.now().isoformat()

                    conn.execute("""
                        INSERT OR REPLACE INTO chunk_embeddings
                        (chunk_id, document_id, embedding, created_at, model_name)
                        VALUES (?, ?, ?, ?, ?)
                    """, (chunk['id'], document_id, embedding_blob, created_at, self.model_name))

                conn.commit()

            logger.info(f"Indexed {len(chunks)} chunks for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            return False

    def search_documents(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> RAGResult:
        """Search for relevant document chunks using semantic similarity."""
        start_time = datetime.now()

        if not self.model or not SKLEARN_AVAILABLE:
            # Fallback to keyword search
            return self._keyword_search_fallback(query, top_k)

        try:
            # Create query embedding
            query_embedding = self.model.encode([query])[0]

            # Get all indexed chunks with embeddings
            matches = []
            documents_searched = set()

            with sqlite3.connect(self.embeddings_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT ce.*, dc.content, dc.chunk_index, dc.page_number, d.original_name, d.file_type
                    FROM chunk_embeddings ce
                    JOIN document_chunks dc ON ce.chunk_id = dc.id
                    JOIN documents d ON ce.document_id = d.id
                    WHERE d.is_indexed = 1 AND d.processing_status = 'completed'
                """)

                for row in cursor.fetchall():
                    documents_searched.add(row['document_id'])

                    # Reconstruct embedding from blob
                    chunk_embedding = np.frombuffer(row['embedding'], dtype=np.float32)

                    # Calculate similarity
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        chunk_embedding.reshape(1, -1)
                    )[0][0]

                    if similarity >= min_similarity:
                        matches.append(DocumentMatch(
                            document_id=row['document_id'],
                            chunk_id=row['chunk_id'],
                            content=row['content'],
                            similarity_score=float(similarity),
                            chunk_index=row['chunk_index'],
                            page_number=row['page_number'],
                            document_title=row['original_name'],
                            document_type=row['file_type']
                        ))

            # Sort by similarity and take top_k
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            top_matches = matches[:top_k]

            # Create context from top matches
            context_parts = []
            for i, match in enumerate(top_matches):
                context_parts.append(f"[Document: {match.document_title}]\n{match.content}")

            context = "\n\n---\n\n".join(context_parts)

            search_time = (datetime.now() - start_time).total_seconds()

            return RAGResult(
                query=query,
                matches=top_matches,
                total_documents_searched=len(documents_searched),
                context_used=context,
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return self._keyword_search_fallback(query, top_k)

    def _keyword_search_fallback(self, query: str, top_k: int) -> RAGResult:
        """Fallback keyword-based search when embeddings are not available."""
        start_time = datetime.now()

        try:
            # Simple keyword search in chunk content
            query_words = query.lower().split()
            matches = []
            documents_searched = set()

            # Get all chunks from indexed documents
            with sqlite3.connect(self.doc_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT dc.*, d.original_name, d.file_type
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.is_indexed = 1 AND d.processing_status = 'completed'
                """)

                for row in cursor.fetchall():
                    documents_searched.add(row['document_id'])
                    content_lower = row['content'].lower()

                    # Count keyword matches
                    match_count = sum(1 for word in query_words if word in content_lower)
                    if match_count > 0:
                        # Simple relevance score based on keyword density
                        relevance = match_count / len(query_words)

                        matches.append(DocumentMatch(
                            document_id=row['document_id'],
                            chunk_id=row['id'],
                            content=row['content'],
                            similarity_score=relevance,
                            chunk_index=row['chunk_index'],
                            page_number=row['page_number'],
                            document_title=row['original_name'],
                            document_type=row['file_type']
                        ))

            # Sort by relevance and take top_k
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            top_matches = matches[:top_k]

            # Create context
            context_parts = []
            for match in top_matches:
                context_parts.append(f"[Document: {match.document_title}]\n{match.content}")

            context = "\n\n---\n\n".join(context_parts)

            search_time = (datetime.now() - start_time).total_seconds()

            return RAGResult(
                query=query,
                matches=top_matches,
                total_documents_searched=len(documents_searched),
                context_used=context,
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"Keyword search fallback failed: {e}")
            return RAGResult(
                query=query,
                matches=[],
                total_documents_searched=0,
                context_used="",
                search_time=(datetime.now() - start_time).total_seconds()
            )

    def get_document_context(self, document_id: str, query: str = None, max_chunks: int = 3) -> str:
        """Get relevant context from a specific document."""
        try:
            if query:
                # Search within specific document
                result = self.search_documents(query, top_k=max_chunks)
                doc_matches = [m for m in result.matches if m.document_id == document_id]

                if doc_matches:
                    context_parts = [match.content for match in doc_matches]
                    return "\n\n".join(context_parts)

            # Fallback: get first few chunks
            chunks = self.doc_db.get_document_chunks(document_id)
            if chunks:
                first_chunks = chunks[:max_chunks]
                return "\n\n".join([chunk['content'] for chunk in first_chunks])

            return ""

        except Exception as e:
            logger.error(f"Failed to get document context: {e}")
            return ""

    def index_all_ready_documents(self) -> Dict[str, Any]:
        """Index all documents that are ready but not yet indexed."""
        results = {
            "indexed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            # Get documents that are completed but not indexed
            ready_docs = self.doc_db.get_all_documents()
            ready_docs = [d for d in ready_docs if d.processing_status == "completed" and not d.is_indexed]

            for doc in ready_docs:
                try:
                    if self.index_document(doc.id):
                        self.doc_db.mark_as_indexed(doc.id)
                        results["indexed"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to index {doc.original_name}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error indexing {doc.original_name}: {str(e)}")

        except Exception as e:
            results["errors"].append(f"Indexing process failed: {str(e)}")

        return results

    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        stats = {
            "embedding_model": self.model_name,
            "model_loaded": self.model is not None,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "sklearn_available": SKLEARN_AVAILABLE
        }

        try:
            # Count embeddings
            with sqlite3.connect(self.embeddings_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM chunk_embeddings")
                stats["total_embeddings"] = cursor.fetchone()[0]

                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT document_id) FROM chunk_embeddings
                """)
                stats["indexed_documents"] = cursor.fetchone()[0]

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def delete_document_embeddings(self, document_id: str) -> bool:
        """Delete embeddings for a document."""
        try:
            with sqlite3.connect(self.embeddings_db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM chunk_embeddings WHERE document_id = ?",
                    (document_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete embeddings for {document_id}: {e}")
            return False