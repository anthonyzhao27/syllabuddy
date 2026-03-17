"""Text extraction from PDF, Word, HTML, and screenshot images."""

import base64
import io
from collections.abc import Awaitable, Callable
from html.parser import HTMLParser
from zipfile import BadZipFile

import fitz
import pdfplumber
from docx import Document
from fastapi import HTTPException, UploadFile
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionContentPartParam

from app.config import settings


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes via PyMuPDF, falling back to pdfplumber."""
    text = ""
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = page.get_text()
                if isinstance(page_text, str):
                    text += page_text
    except Exception:
        pass

    if len(text.strip()) < 50:
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass

    return text.strip()


def _pdf_pages_to_base64_images(
    data: bytes, max_pages: int = 20, dpi: int = 200
) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images for vision API."""
    images: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for i in range(min(len(doc), max_pages)):
            page = doc[i]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            images.append(base64.b64encode(img_bytes).decode("utf-8"))
    return images


async def _extract_pdf_via_vision(data: bytes) -> str:
    """Use OpenAI vision to OCR scanned PDF pages."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    images = _pdf_pages_to_base64_images(data)
    if not images:
        return ""

    content: list[ChatCompletionContentPartParam] = [
        {
            "type": "text",
            "text": (
                "Extract ALL text from these scanned syllabus pages. "
                "Return the raw text only, preserving structure like tables and lists. "
                "Do not summarize."
            ),
        },
    ]
    for img_b64 in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "high",
                },
            }
        )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=4096,
    )

    result = response.choices[0].message.content
    return result.strip() if result else ""


async def _extract_pdf(data: bytes) -> str:
    """Extract text from PDF. Tries text extraction first, falls back to vision."""
    try:
        text = _extract_pdf_text(data)
    except fitz.FileDataError:
        raise HTTPException(
            status_code=422, detail="PDF appears to be password-protected or corrupt."
        )

    if len(text.strip()) < 50:
        try:
            vision_text = await _extract_pdf_via_vision(data)
            if vision_text:
                return vision_text
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="OCR failed — try uploading a text-based PDF instead.",
            )

    return text


def _extract_docx(data: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        doc = Document(io.BytesIO(data))
    except BadZipFile:
        raise HTTPException(status_code=422, detail="DOCX file appears to be corrupt.")

    parts: list[str] = []

    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)

    for table in doc.tables:
        for row in table.rows:
            row_text = "\t".join(cell.text.strip() for cell in row.cells)
            if row_text.strip():
                parts.append(row_text)

    return "\n".join(parts)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _extract_html(data: bytes) -> str:
    """Extract visible text from HTML bytes."""
    parser = _HTMLTextExtractor()
    parser.feed(data.decode("utf-8", errors="replace"))
    return parser.get_text().strip()


async def _extract_images_via_vision(images_data: list[bytes]) -> str:
    """Use OpenAI vision to extract text from one or more screenshot images."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    content: list[ChatCompletionContentPartParam] = [
        {
            "type": "text",
            "text": (
                "These are screenshots of a course syllabus or assignment page. "
                "Extract ALL text from every image. Return the raw text only, "
                "preserving structure like tables, dates, and lists. "
                "Combine text across images into one coherent document. Do not summarize."
            ),
        },
    ]
    for img_bytes in images_data:
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        mime = "image/png" if img_bytes[:4] == b"\x89PNG" else "image/jpeg"
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"},
            }
        )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=4096,
    )

    result = response.choices[0].message.content
    return result.strip() if result else ""


IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

SyncHandler = Callable[[bytes], str]
AsyncHandler = Callable[[bytes], Awaitable[str]]
Handler = SyncHandler | AsyncHandler

CONTENT_TYPE_MAP: dict[str, Handler] = {
    "application/pdf": _extract_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": _extract_docx,
    "text/html": _extract_html,
}

EXTENSION_MAP: dict[str, Handler] = {
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
    ".html": _extract_html,
    ".htm": _extract_html,
}


def _is_image(file: UploadFile) -> bool:
    """Check if the file is an image based on content type or extension."""
    if file.content_type in IMAGE_CONTENT_TYPES:
        return True
    if file.filename:
        ext = (
            "." + file.filename.rsplit(".", 1)[-1].lower()
            if "." in file.filename
            else ""
        )
        return ext in {".png", ".jpg", ".jpeg", ".webp"}
    return False


async def extract_text(file: UploadFile) -> str:
    """Extract plain text from a single uploaded document."""
    data = await file.read()

    handler: Handler | None = CONTENT_TYPE_MAP.get(file.content_type or "")

    if handler is None and file.filename:
        ext = (
            "." + file.filename.rsplit(".", 1)[-1].lower()
            if "." in file.filename
            else ""
        )
        handler = EXTENSION_MAP.get(ext)

    if handler is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type} ({file.filename})",
        )

    import asyncio

    if asyncio.iscoroutinefunction(handler):
        text = await handler(data)
    else:
        text = handler(data)  # type: ignore[misc]

    if not text:
        raise HTTPException(
            status_code=422, detail="Could not extract any text from the file."
        )

    return text  # type: ignore[return-value]


async def extract_text_from_images(files: list[UploadFile]) -> str:
    """Extract text from multiple screenshot images via LLM vision."""
    images_data: list[bytes] = []
    for f in files:
        data = await f.read()
        if not data:
            continue
        images_data.append(data)

    if not images_data:
        raise HTTPException(status_code=400, detail="No valid images provided.")

    if len(images_data) > 10:
        raise HTTPException(
            status_code=400, detail="Maximum 10 screenshots per request."
        )

    text = await _extract_images_via_vision(images_data)
    if not text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the screenshots.",
        )

    return text
