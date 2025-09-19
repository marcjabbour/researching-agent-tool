"""
Document Management API Routes
Handles document upload, processing, and management endpoints.
"""

import os
import asyncio
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .document_database import DocumentDatabase, DocumentRecord
from .document_processor import DocumentProcessor
from .rag_service import RAGService, DocumentMatch, RAGResult


# Initialize services
doc_db = DocumentDatabase()
doc_processor = DocumentProcessor()
rag_service = RAGService()

# Create router
router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_time: str
    processing_status: str
    processing_error: Optional[str] = None
    content_preview: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    is_indexed: bool
    tags: List[str]


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[DocumentResponse]
    total_count: int


class DocumentStatsResponse(BaseModel):
    """Document statistics response model."""
    total_documents: int
    processed_documents: int
    indexed_documents: int
    failed_documents: int
    total_size_bytes: int
    file_types: dict


class DocumentMatchResponse(BaseModel):
    """Document match response model."""
    document_id: str
    chunk_id: str
    content: str
    similarity_score: float
    chunk_index: int
    page_number: Optional[int] = None
    document_title: str
    document_type: str


class RAGSearchResponse(BaseModel):
    """RAG search response model."""
    query: str
    matches: List[DocumentMatchResponse]
    total_documents_searched: int
    context_used: str
    search_time: float


class RAGStatsResponse(BaseModel):
    """RAG statistics response model."""
    embedding_model: str
    model_loaded: bool
    sentence_transformers_available: bool
    sklearn_available: bool
    total_embeddings: Optional[int] = None
    indexed_documents: Optional[int] = None
    error: Optional[str] = None


def _convert_record_to_response(record: DocumentRecord) -> DocumentResponse:
    """Convert database record to API response."""
    return DocumentResponse(
        id=record.id,
        filename=record.filename,
        original_name=record.original_name,
        file_type=record.file_type,
        file_size=record.file_size,
        upload_time=record.upload_time,
        processing_status=record.processing_status,
        processing_error=record.processing_error,
        content_preview=record.content_preview,
        page_count=record.page_count,
        word_count=record.word_count,
        is_indexed=record.is_indexed,
        tags=record.tags
    )


def _convert_match_to_response(match: DocumentMatch) -> DocumentMatchResponse:
    """Convert RAG match to API response."""
    return DocumentMatchResponse(
        document_id=match.document_id,
        chunk_id=match.chunk_id,
        content=match.content,
        similarity_score=match.similarity_score,
        chunk_index=match.chunk_index,
        page_number=match.page_number,
        document_title=match.document_title,
        document_type=match.document_type
    )


async def _process_document_background(doc_id: str, file_path: str, file_type: str):
    """Background task to process uploaded document."""
    try:
        # Update status to processing
        doc_db.update_processing_status(doc_id, "processing")

        # Process the document
        result = await doc_processor.process_document_async(file_path, file_type)

        if result.success:
            # Update database with processing results
            preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
            doc_db.update_processing_status(
                doc_id, "completed", None, preview,
                result.page_count, result.word_count
            )

            # Store chunks for RAG
            if result.chunks:
                for chunk in result.chunks:
                    doc_db.add_document_chunk(
                        doc_id, chunk["chunk_index"], chunk["content"],
                        chunk.get("page_number"), chunk["start_char"], chunk["end_char"]
                    )

            # Mark as indexed and create vector embeddings
            doc_db.mark_as_indexed(doc_id)

            # Index document for RAG
            rag_service.index_document(doc_id)

        else:
            # Update with error status
            doc_db.update_processing_status(doc_id, "failed", result.error)

    except Exception as e:
        # Update with error status
        doc_db.update_processing_status(doc_id, "failed", str(e))


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tags: str = Form("[]")  # JSON string of tags
):
    """Upload and process a document."""
    try:
        # Validate file type
        supported_types = doc_processor.get_supported_file_types()
        file_extension = file.filename.split(".")[-1].lower() if file.filename else ""

        all_supported = supported_types["documents"] + supported_types["spreadsheets"]
        if file_extension not in all_supported:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(all_supported)}"
            )

        # Validate file size (50MB limit)
        content = await file.read()
        max_size = supported_types["max_size_mb"] * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {supported_types['max_size_mb']}MB"
            )

        # Save file
        saved_path = doc_processor.save_uploaded_file(content, file.filename)

        # Parse tags
        import json
        try:
            tag_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            tag_list = []

        # Create database record
        doc_id = doc_db.create_document(
            filename=os.path.basename(saved_path),
            original_name=file.filename,
            file_type=file_extension,
            file_size=len(content),
            tags=tag_list
        )

        # Start background processing
        background_tasks.add_task(_process_document_background, doc_id, saved_path, file_extension)

        # Get and return the created document
        record = doc_db.get_document(doc_id)
        return _convert_record_to_response(record)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(status: Optional[str] = None, limit: int = 50):
    """Get list of documents, optionally filtered by status."""
    try:
        records = doc_db.get_all_documents(status_filter=status)
        limited_records = records[:limit]

        return DocumentListResponse(
            documents=[_convert_record_to_response(record) for record in limited_records],
            total_count=len(records)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats():
    """Get document collection statistics."""
    try:
        stats = doc_db.get_document_stats()
        return DocumentStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get document details by ID."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        return _convert_record_to_response(record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its associated data."""
    try:
        # Get document info for file cleanup
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database
        success = doc_db.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        # Clean up file
        file_path = os.path.join(doc_processor.upload_dir, record.filename)
        doc_processor.delete_file(file_path)

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/content")
async def get_document_content(doc_id: str):
    """Get full document content."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        if record.processing_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Document not ready. Status: {record.processing_status}"
            )

        # Get chunks and reconstruct content
        chunks = doc_db.get_document_chunks(doc_id)
        full_content = "\n\n".join([chunk["content"] for chunk in chunks])

        return {
            "document_id": doc_id,
            "content": full_content,
            "chunk_count": len(chunks),
            "word_count": record.word_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/chunks")
async def get_document_chunks(doc_id: str):
    """Get document chunks for debugging/inspection."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks = doc_db.get_document_chunks(doc_id)
        return {
            "document_id": doc_id,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-types/list")
async def get_supported_file_types():
    """Get list of supported file types and limits."""
    return doc_processor.get_supported_file_types()


@router.post("/{doc_id}/reprocess")
async def reprocess_document(doc_id: str, background_tasks: BackgroundTasks):
    """Reprocess a document that failed or needs updating."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = os.path.join(doc_processor.upload_dir, record.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="Source file no longer exists")

        # Start reprocessing
        background_tasks.add_task(_process_document_background, doc_id, file_path, record.file_type)

        return {"message": "Document reprocessing started"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# RAG Endpoints
@router.post("/search", response_model=RAGSearchResponse)
async def search_documents_rag(
    query: str = Form(...),
    top_k: int = Form(5),
    min_similarity: float = Form(0.3)
):
    """Search documents using RAG (semantic similarity)."""
    try:
        result = rag_service.search_documents(query, top_k, min_similarity)

        return RAGSearchResponse(
            query=result.query,
            matches=[_convert_match_to_response(match) for match in result.matches],
            total_documents_searched=result.total_documents_searched,
            context_used=result.context_used,
            search_time=result.search_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats", response_model=RAGStatsResponse)
async def get_rag_stats():
    """Get RAG service statistics."""
    try:
        stats = rag_service.get_rag_stats()
        return RAGStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/index-all")
async def index_all_documents(background_tasks: BackgroundTasks):
    """Index all ready documents for RAG."""
    try:
        def index_task():
            return rag_service.index_all_ready_documents()

        background_tasks.add_task(index_task)
        return {"message": "Document indexing started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{doc_id}/index")
async def index_document(doc_id: str, background_tasks: BackgroundTasks):
    """Index a specific document for RAG."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        if record.processing_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Document not ready for indexing. Status: {record.processing_status}"
            )

        def index_task():
            success = rag_service.index_document(doc_id)
            if success:
                doc_db.mark_as_indexed(doc_id)
            return success

        background_tasks.add_task(index_task)
        return {"message": f"Document {doc_id} indexing started"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}/context")
async def get_document_context(doc_id: str, query: str = None, max_chunks: int = 3):
    """Get relevant context from a specific document."""
    try:
        record = doc_db.get_document(doc_id)
        if not record:
            raise HTTPException(status_code=404, detail="Document not found")

        context = rag_service.get_document_context(doc_id, query, max_chunks)

        return {
            "document_id": doc_id,
            "document_title": record.original_name,
            "query": query,
            "context": context,
            "max_chunks": max_chunks
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))