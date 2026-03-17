"""Integration tests for the /parse endpoint."""

import struct
import zlib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import ParsedEvent

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)


def _mock_events() -> list[ParsedEvent]:
    return [
        ParsedEvent(
            title="Homework 1",
            due_date=datetime(2025, 1, 30),
            course="CS 101",
            event_type="assignment",
        )
    ]


def _tiny_png() -> bytes:
    raw = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    chunks = b""
    for ctype, cdata in [
        (b"IHDR", ihdr),
        (b"IDAT", compressed),
        (b"IEND", b""),
    ]:
        crc = zlib.crc32(ctype + cdata) & 0xFFFFFFFF
        chunks += struct.pack(">I", len(cdata)) + ctype + cdata + struct.pack(">I", crc)
    return b"\x89PNG\r\n\x1a\n" + chunks


@patch(
    "app.routers.parse.extract_events",
    new_callable=AsyncMock,
)
def test_parse_pdf_upload(mock_llm: AsyncMock) -> None:
    mock_llm.return_value = _mock_events()
    pdf_bytes = (FIXTURES / "sample.pdf").read_bytes()
    resp = client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )
    assert resp.status_code == 200
    assert len(resp.json()["events"]) == 1


@patch(
    "app.routers.parse.extract_events",
    new_callable=AsyncMock,
)
@patch(
    "app.routers.parse.fetch_google_doc",
    new_callable=AsyncMock,
    return_value="some text",
)
def test_parse_google_doc(mock_gdoc: AsyncMock, mock_llm: AsyncMock) -> None:
    mock_llm.return_value = _mock_events()
    resp = client.post(
        "/parse/",
        data={"google_doc_url": "https://docs.google.com/document/d/abc/edit"},
    )
    assert resp.status_code == 200


@patch(
    "app.routers.parse.extract_events",
    new_callable=AsyncMock,
)
@patch(
    "app.routers.parse.extract_text_from_images",
    new_callable=AsyncMock,
    return_value="Quiz 1 due Feb 14",
)
def test_parse_screenshot_batch(mock_vision: AsyncMock, mock_llm: AsyncMock) -> None:
    """Multiple screenshot images are processed via vision."""
    mock_llm.return_value = _mock_events()
    png = _tiny_png()
    resp = client.post(
        "/parse/",
        files=[
            ("files", ("screen1.png", png, "image/png")),
            ("files", ("screen2.png", png, "image/png")),
        ],
    )
    assert resp.status_code == 200
    mock_vision.assert_called_once()


def test_parse_no_input() -> None:
    resp = client.post("/parse/")
    assert resp.status_code in (400, 422)
