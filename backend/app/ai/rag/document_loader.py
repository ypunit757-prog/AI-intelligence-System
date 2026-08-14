"""Extracts plain text from supported document types.

Supported: PDF, DOCX, TXT, Markdown, CSV, JSON, and common source code
file extensions (treated as plain text).
"""
import io
import json

from docx import Document as DocxDocument
from pypdf import PdfReader

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".csv"}


def extract_text(filename: str, data: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if lower.endswith(".docx"):
        doc = DocxDocument(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)

    if lower.endswith(".json"):
        try:
            parsed = json.loads(data.decode("utf-8"))
            return json.dumps(parsed, indent=2)
        except Exception:
            return data.decode("utf-8", errors="ignore")

    if any(lower.endswith(ext) for ext in TEXT_EXTENSIONS):
        return data.decode("utf-8", errors="ignore")

    # Fallback: best-effort decode
    return data.decode("utf-8", errors="ignore")


ALLOWED_EXTENSIONS = TEXT_EXTENSIONS | {".pdf", ".docx", ".json"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
