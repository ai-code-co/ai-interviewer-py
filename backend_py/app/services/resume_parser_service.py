## backend_py/app/services/resume_parser_service.py
from __future__ import annotations

from dataclasses import dataclass
import io  # <--- IMPORT IO
import docx  # python-docx
import pdfplumber


@dataclass
class ParseResult:
    text: str
    word_count: int


def _clean_text(text: str) -> str:
    """
    Clean extracted text:
    - Remove excessive whitespace
    - Remove some common header/footer patterns
    - Limit to ~32k characters (~8k tokens)
    """
    import re

    cleaned = re.sub(r"\s+", " ", text or "").strip()

    cleaned = re.sub(r"(Page \d+ of \d+|Confidential|Resume|Curriculum Vitae)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "",
        cleaned,
    )
    cleaned = re.sub(
        r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "",
        cleaned,
    )

    max_length = 32000
    if len(cleaned) > max_length:
        truncated = cleaned[:max_length]
        last_period = truncated.rfind(".")
        if last_period > int(max_length * 0.9):
            cleaned = truncated[: last_period + 1]
        else:
            cleaned = truncated + "..."

    return cleaned.strip()


def _parse_pdf(buffer: bytes) -> ParseResult:
    try:
        # FIX: Wrap raw bytes in io.BytesIO so pdfplumber can .seek()
        with pdfplumber.open(io.BytesIO(buffer)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        
        text = _clean_text(" ".join(pages_text))
        words = [w for w in text.split() if w]
        return ParseResult(text=text, word_count=len(words))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to parse PDF: {exc}") from exc


def _parse_docx(buffer: bytes) -> ParseResult:
    try:
        # docx also requires a file-like object
        document = docx.Document(io.BytesIO(buffer))
        paragraphs = [p.text for p in document.paragraphs]
        text = _clean_text(" ".join(paragraphs))
        words = [w for w in text.split() if w]
        return ParseResult(text=text, word_count=len(words))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to parse DOCX: {exc}") from exc


def extract_resume_text(buffer: bytes, filename: str) -> ParseResult:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _parse_pdf(buffer)
    if lower.endswith(".docx") or lower.endswith(".doc"):
        return _parse_docx(buffer)
    raise RuntimeError("Unsupported resume format. Only PDF and DOCX files are supported.")