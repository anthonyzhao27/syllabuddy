"""Tests for text extraction service."""

import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.extraction import (
    _extract_docx,
    _extract_html,
    _extract_pdf,
    _extract_pdf_text,
    _is_image,
    _pdf_pages_to_base64_images,
    extract_text,
    extract_text_from_images,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ── PDF ──────────────────────────────────────────────


def test_extract_pdf_text() -> None:
    data = (FIXTURES / "sample.pdf").read_bytes()
    text = _extract_pdf_text(data)
    assert "Homework 1" in text
    assert "January 30" in text


# ── DOCX ─────────────────────────────────────────────


def test_extract_docx() -> None:
    data = (FIXTURES / "sample.docx").read_bytes()
    text = _extract_docx(data)
    assert "Midterm Exam" in text
    assert "Quiz 1" in text


# ── HTML ─────────────────────────────────────────────


def test_extract_html() -> None:
    data = (FIXTURES / "sample.html").read_bytes()
    text = _extract_html(data)
    assert "Final Project" in text
    assert "var x" not in text


# ── Dispatcher ───────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_text_pdf() -> None:
    file = AsyncMock()
    file.content_type = "application/pdf"
    file.filename = "syllabus.pdf"
    file.read = AsyncMock(return_value=(FIXTURES / "sample.pdf").read_bytes())

    text = await extract_text(file)
    assert "Homework 1" in text


@pytest.mark.asyncio
async def test_extract_text_unsupported() -> None:
    file = AsyncMock()
    file.content_type = "image/png"
    file.filename = "photo.png"
    file.read = AsyncMock(return_value=b"fake")

    with pytest.raises(HTTPException) as exc:
        await extract_text(file)
    assert exc.value.status_code == 400


# ── Vision fallback ─────────────────────────────────


@pytest.mark.asyncio
async def test_extract_pdf_falls_back_to_vision() -> None:
    """When text extraction returns < 50 chars, vision fallback is triggered."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(50, 50, 100, 100), color=(0, 0, 0))
    scanned_pdf = doc.tobytes()
    doc.close()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Homework 1 due January 30, 2025"

    with patch("app.services.extraction.AsyncOpenAI") as MockClient:
        instance = AsyncMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        MockClient.return_value = instance

        text = await _extract_pdf(scanned_pdf)
        assert "Homework 1" in text
        instance.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_extract_pdf_skips_vision_when_text_found() -> None:
    """When text extraction succeeds, vision is NOT called."""
    data = (FIXTURES / "sample.pdf").read_bytes()

    with patch("app.services.extraction._extract_pdf_via_vision") as mock_vision:
        text = await _extract_pdf(data)
        assert "Homework 1" in text
        mock_vision.assert_not_called()


def test_pdf_pages_to_base64_images() -> None:
    """Verify page-to-image conversion produces valid base64."""
    data = (FIXTURES / "sample.pdf").read_bytes()
    images = _pdf_pages_to_base64_images(data, max_pages=1)
    assert len(images) == 1
    decoded = base64.b64decode(images[0])
    assert decoded[:4] == b"\x89PNG"


# ── Screenshot extraction ────────────────────────────


@pytest.mark.asyncio
async def test_extract_text_from_images() -> None:
    """Multi-image screenshot extraction calls vision with all images."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Quiz 1 due Feb 14, 2025"

    fake_png = b"\x89PNG" + b"\x00" * 100
    file1 = AsyncMock()
    file1.read = AsyncMock(return_value=fake_png)
    file2 = AsyncMock()
    file2.read = AsyncMock(return_value=fake_png)

    with patch("app.services.extraction.AsyncOpenAI") as MockClient:
        instance = AsyncMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        MockClient.return_value = instance

        text = await extract_text_from_images([file1, file2])
        assert "Quiz 1" in text

        call_args = instance.chat.completions.create.call_args
        msg_content = call_args.kwargs["messages"][0]["content"]
        image_parts = [c for c in msg_content if c["type"] == "image_url"]
        assert len(image_parts) == 2


@pytest.mark.asyncio
async def test_extract_text_from_images_too_many() -> None:
    """Reject more than 10 screenshots."""
    files = []
    for _ in range(11):
        f = AsyncMock()
        f.read = AsyncMock(return_value=b"\x89PNG" + b"\x00" * 10)
        files.append(f)

    with pytest.raises(HTTPException) as exc:
        await extract_text_from_images(files)
    assert exc.value.status_code == 400
    assert "10" in exc.value.detail


def test_is_image_detection() -> None:
    """_is_image correctly identifies image uploads."""
    img_file = MagicMock()
    img_file.content_type = "image/png"
    img_file.filename = "screenshot.png"
    assert _is_image(img_file) is True

    pdf_file = MagicMock()
    pdf_file.content_type = "application/pdf"
    pdf_file.filename = "syllabus.pdf"
    assert _is_image(pdf_file) is False
