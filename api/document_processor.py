"""
Document Processing Service
Handles document parsing, text extraction, and chunking for RAG.
"""

import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# Document processing libraries
try:
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import pandas as pd
except ImportError:
    pd = None

from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    content: str
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    error: Optional[str] = None
    chunks: List[Dict[str, Any]] = None


class DocumentProcessor:
    """Service for processing uploaded documents."""

    def __init__(self, upload_dir: str = "uploads", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_document_async(self, file_path: str, file_type: str) -> ProcessingResult:
        """Process document asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._process_document_sync, file_path, file_type
        )

    def _process_document_sync(self, file_path: str, file_type: str) -> ProcessingResult:
        """Synchronous document processing."""
        try:
            if file_type.lower() == 'pdf':
                return self._process_pdf(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                return self._process_docx(file_path)
            elif file_type.lower() == 'txt':
                return self._process_text(file_path)
            elif file_type.lower() in ['csv', 'xlsx', 'xls']:
                return self._process_spreadsheet(file_path, file_type)
            else:
                return ProcessingResult(
                    success=False,
                    content="",
                    error=f"Unsupported file type: {file_type}"
                )

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                content="",
                error=f"Processing failed: {str(e)}"
            )

    def _process_pdf(self, file_path: str) -> ProcessingResult:
        """Process PDF documents."""
        if not PyPDF2:
            return ProcessingResult(
                success=False,
                content="",
                error="PyPDF2 not installed. Install with: pip install PyPDF2"
            )

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                page_count = len(pdf_reader.pages)

                content_parts = []
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        content_parts.append(text)

                full_content = "\n\n".join(content_parts)
                word_count = len(full_content.split())

                chunks = self._create_chunks(full_content, file_type="pdf")

                return ProcessingResult(
                    success=True,
                    content=full_content,
                    page_count=page_count,
                    word_count=word_count,
                    chunks=chunks
                )

        except Exception as e:
            return ProcessingResult(
                success=False,
                content="",
                error=f"PDF processing failed: {str(e)}"
            )

    def _process_docx(self, file_path: str) -> ProcessingResult:
        """Process DOCX documents."""
        if not DocxDocument:
            return ProcessingResult(
                success=False,
                content="",
                error="python-docx not installed. Install with: pip install python-docx"
            )

        try:
            doc = DocxDocument(file_path)
            content_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content_parts.append(paragraph.text)

            full_content = "\n\n".join(content_parts)
            word_count = len(full_content.split())
            chunks = self._create_chunks(full_content, file_type="docx")

            return ProcessingResult(
                success=True,
                content=full_content,
                word_count=word_count,
                chunks=chunks
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                content="",
                error=f"DOCX processing failed: {str(e)}"
            )

    def _process_text(self, file_path: str) -> ProcessingResult:
        """Process plain text files."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = ""

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue

            if not content:
                return ProcessingResult(
                    success=False,
                    content="",
                    error="Could not decode text file with any standard encoding"
                )

            word_count = len(content.split())
            chunks = self._create_chunks(content, file_type="txt")

            return ProcessingResult(
                success=True,
                content=content,
                word_count=word_count,
                chunks=chunks
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                content="",
                error=f"Text processing failed: {str(e)}"
            )

    def _process_spreadsheet(self, file_path: str, file_type: str) -> ProcessingResult:
        """Process spreadsheet files (CSV, Excel)."""
        if not pd:
            return ProcessingResult(
                success=False,
                content="",
                error="pandas not installed. Install with: pip install pandas openpyxl"
            )

        try:
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Convert to readable format
            content_parts = []
            content_parts.append(f"Spreadsheet Summary:")
            content_parts.append(f"- Rows: {len(df)}")
            content_parts.append(f"- Columns: {len(df.columns)}")
            content_parts.append(f"- Column Names: {', '.join(df.columns.tolist())}")
            content_parts.append("\nFirst 10 rows:")
            content_parts.append(df.head(10).to_string())

            if len(df) > 10:
                content_parts.append(f"\n... and {len(df) - 10} more rows")

            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                content_parts.append("\nNumeric Column Statistics:")
                content_parts.append(df[numeric_cols].describe().to_string())

            full_content = "\n\n".join(content_parts)
            word_count = len(full_content.split())
            chunks = self._create_chunks(full_content, file_type=file_type)

            return ProcessingResult(
                success=True,
                content=full_content,
                word_count=word_count,
                chunks=chunks
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                content="",
                error=f"Spreadsheet processing failed: {str(e)}"
            )

    def _create_chunks(self, content: str, file_type: str) -> List[Dict[str, Any]]:
        """Create text chunks for RAG processing."""
        if not content.strip():
            return []

        chunks = []
        words = content.split()

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            if chunk_text.strip():
                chunks.append({
                    "chunk_index": len(chunks),
                    "content": chunk_text,
                    "start_char": content.find(chunk_words[0]) if chunk_words else 0,
                    "end_char": content.rfind(chunk_words[-1]) + len(chunk_words[-1]) if chunk_words else 0,
                    "word_count": len(chunk_words)
                })

        return chunks

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return the file path."""
        # Create unique filename to avoid conflicts
        file_path = self.upload_dir / filename
        counter = 1
        original_path = file_path

        while file_path.exists():
            name_parts = original_path.stem, counter, original_path.suffix
            file_path = self.upload_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            counter += 1

        with open(file_path, 'wb') as f:
            f.write(file_content)

        return str(file_path)

    def delete_file(self, file_path: str) -> bool:
        """Delete processed file."""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information."""
        try:
            path = Path(file_path)
            stat = path.stat()

            return {
                "filename": path.name,
                "size": stat.st_size,
                "extension": path.suffix.lower(),
                "exists": path.exists()
            }
        except Exception:
            return {
                "filename": "",
                "size": 0,
                "extension": "",
                "exists": False
            }

    @staticmethod
    def get_supported_file_types() -> Dict[str, List[str]]:
        """Get list of supported file types."""
        return {
            "documents": ["pdf", "docx", "doc", "txt"],
            "spreadsheets": ["csv", "xlsx", "xls"],
            "max_size_mb": 50  # Maximum file size in MB
        }

    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old uploaded files."""
        try:
            import time
            current_time = time.time()

            for file_path in self.upload_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (days_old * 24 * 60 * 60):  # Convert days to seconds
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")