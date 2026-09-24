"""Integration tests for the /parse endpoint."""

import struct
import zlib
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.schemas import ParsedEvent

_STALE_SAVE_FLOW = pytest.mark.skip(
    reason=(
        "Stale: /parse no longer saves; persistence is now covered by "
        "test_files_router.py against POST /files/."
    )
)


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


def test_parse_requires_auth(api_client: TestClient, generated_pdf_path) -> None:
    pdf_bytes = generated_pdf_path.read_bytes()
    resp = api_client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )
    assert resp.status_code == 401


@_STALE_SAVE_FLOW
@patch(
    "app.routers.parse.extract_events",
    new_callable=AsyncMock,
)
@patch("app.routers.parse.storage_service.upload_files", new_callable=AsyncMock)
@patch("app.routers.parse.syllabi_service.create_syllabus", new_callable=AsyncMock)
@patch("app.routers.parse.syllabi_service.save_events", new_callable=AsyncMock)
def test_parse_pdf_upload(
    mock_save_events: AsyncMock,
    mock_create_syllabus: AsyncMock,
    mock_upload_files: AsyncMock,
    mock_llm: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    mock_llm.return_value = _mock_events()
    mock_upload_files.return_value = {
        "paths": ["00000000-0000-0000-0000-000000000001/syllabus.pdf"],
        "total_size": 1234,
    }
    mock_create_syllabus.return_value = {"id": "syllabus-123"}
    pdf_bytes = generated_pdf_path.read_bytes()
    resp = authenticated_client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )
    assert resp.status_code == 200
    assert resp.json()["syllabus_id"] == "syllabus-123"
    assert len(resp.json()["events"]) == 1
    mock_save_events.assert_awaited_once()


@_STALE_SAVE_FLOW
@patch(
    "app.routers.parse.extract_events",
    new_callable=AsyncMock,
)
@patch(
    "app.routers.parse.extract_text_from_images",
    new_callable=AsyncMock,
    return_value="Quiz 1 due Feb 14",
)
@patch("app.routers.parse.storage_service.upload_files", new_callable=AsyncMock)
@patch("app.routers.parse.syllabi_service.create_syllabus", new_callable=AsyncMock)
@patch("app.routers.parse.syllabi_service.save_events", new_callable=AsyncMock)
def test_parse_screenshot_batch(
    mock_save_events: AsyncMock,
    mock_create_syllabus: AsyncMock,
    mock_upload_files: AsyncMock,
    mock_vision: AsyncMock,
    mock_llm: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    """Multiple screenshot images are processed via vision."""
    mock_llm.return_value = _mock_events()
    mock_upload_files.return_value = {
        "paths": ["00000000-0000-0000-0000-000000000001/screen1.png"],
        "total_size": 1234,
    }
    mock_create_syllabus.return_value = {"id": "syllabus-456"}
    png = _tiny_png()
    resp = authenticated_client.post(
        "/parse/",
        files=[
            ("files", ("screen1.png", png, "image/png")),
            ("files", ("screen2.png", png, "image/png")),
        ],
    )
    assert resp.status_code == 200
    assert resp.json()["syllabus_id"] == "syllabus-456"
    mock_vision.assert_called_once()


def test_parse_no_input(authenticated_client: TestClient) -> None:
    resp = authenticated_client.post("/parse/")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Please upload a file."


@patch("app.routers.parse.extract_text_from_images", new_callable=AsyncMock)
def test_parse_rejects_mixed_screenshot_batch(
    mock_vision: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    png = _tiny_png()
    pdf_bytes = generated_pdf_path.read_bytes()
    resp = authenticated_client.post(
        "/parse/",
        files=[
            ("files", ("screen1.png", png, "image/png")),
            ("files", ("syllabus.pdf", pdf_bytes, "application/pdf")),
        ],
    )
    assert resp.status_code == 400
    assert (
        resp.json()["detail"] == "When uploading screenshots, all files must be images."
    )
    mock_vision.assert_not_awaited()


@patch(
    "app.routers.parse.storage_service.validate_total_upload_size",
    new_callable=AsyncMock,
    side_effect=HTTPException(status_code=400, detail="File size exceeds 10MB limit"),
)
@patch("app.routers.parse.extract_text", new_callable=AsyncMock)
def test_parse_rejects_oversized_upload_before_extraction(
    mock_extract_text: AsyncMock,
    mock_validate_size: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    pdf_bytes = generated_pdf_path.read_bytes()
    resp = authenticated_client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "File size exceeds 10MB limit"
    mock_extract_text.assert_not_awaited()


@_STALE_SAVE_FLOW
@patch(
    "app.routers.parse.extract_text",
    new_callable=AsyncMock,
    return_value="Homework 1 due January 30",
)
@patch("app.routers.parse.extract_events", new_callable=AsyncMock)
@patch(
    "app.routers.parse.storage_service.upload_files",
    new_callable=AsyncMock,
    side_effect=RuntimeError("storage unavailable"),
)
@patch("app.routers.parse.syllabi_service.create_syllabus", new_callable=AsyncMock)
def test_parse_returns_503_when_upload_fails(
    mock_create_syllabus: AsyncMock,
    mock_upload_files: AsyncMock,
    mock_extract_events: AsyncMock,
    mock_extract_text: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    mock_extract_events.return_value = _mock_events()
    pdf_bytes = generated_pdf_path.read_bytes()
    resp = authenticated_client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Failed to save parsed syllabus. Please try again."
    mock_upload_files.assert_awaited_once()
    mock_create_syllabus.assert_not_awaited()


@_STALE_SAVE_FLOW
@patch(
    "app.routers.parse.extract_text",
    new_callable=AsyncMock,
    return_value="Homework 1 due January 30",
)
@patch("app.routers.parse.extract_events", new_callable=AsyncMock)
@patch("app.routers.parse.storage_service.upload_files", new_callable=AsyncMock)
@patch(
    "app.routers.parse.storage_service.delete_file_best_effort",
    new_callable=AsyncMock,
)
@patch("app.routers.parse.syllabi_service.create_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.parse.syllabi_service.save_events",
    new_callable=AsyncMock,
    side_effect=RuntimeError("insert failed"),
)
@patch("app.routers.parse.syllabi_service.delete_syllabus", new_callable=AsyncMock)
def test_parse_cleans_up_when_event_save_fails(
    mock_delete_syllabus: AsyncMock,
    mock_save_events: AsyncMock,
    mock_create_syllabus: AsyncMock,
    mock_delete_file_best_effort: AsyncMock,
    mock_upload_files: AsyncMock,
    mock_extract_events: AsyncMock,
    mock_extract_text: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    mock_extract_events.return_value = _mock_events()
    mock_upload_files.return_value = {
        "paths": [
            "00000000-0000-0000-0000-000000000001/file1.pdf",
            "00000000-0000-0000-0000-000000000001/file2.pdf",
        ],
        "total_size": 1234,
    }
    mock_create_syllabus.return_value = {"id": "syllabus-123"}

    pdf_bytes = generated_pdf_path.read_bytes()
    resp = authenticated_client.post(
        "/parse/",
        files=[("files", ("syllabus.pdf", pdf_bytes, "application/pdf"))],
    )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Failed to save parsed syllabus. Please try again."
    assert mock_delete_file_best_effort.await_count == 2
    mock_delete_syllabus.assert_awaited_once_with("test-token", "syllabus-123")


_EXTRACTION = {
    "course_code": "CSC263H1S",
    "term": {"season": "winter", "year": 2026, "campus": "st_george", "evidence": ""},
    "schedule_anchor": {
        "week1_month": None,
        "week1_day": None,
        "evidence": "",
        "reading_week_numbered": False,
    },
    "meetings": [],
    "week_dates": [],
    "events": [
        {
            "title": "Essay",
            "event_type": "assignment",
            "description": "",
            "date_kind": "week",
            "date": None,
            "stated_weekday": None,
            "week": 3,
            "in_class": False,
            "meeting_kind": None,
            "time": None,
            "duration_minutes": None,
            "source_text": "Week 3: essay",
        }
    ],
    "recurring": [],
}


@patch("app.routers.parse.extract_text", new_callable=AsyncMock)
@patch("app.routers.parse.extract_syllabus", new_callable=AsyncMock)
def test_parse_returns_term_context_and_extraction(
    mock_extract: AsyncMock,
    mock_extract_text: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    from datetime import date

    from app.models.schemas import LLMSyllabus
    from app.services.llm import ExtractionOutcome, resolve_extraction

    ext = LLMSyllabus.model_validate(_EXTRACTION)
    events, ctx = resolve_extraction(ext, date(2025, 12, 29))
    mock_extract_text.return_value = "syllabus text"
    mock_extract.return_value = ExtractionOutcome(
        events=events, term_context=ctx, extraction=ext, raw=""
    )
    resp = authenticated_client.post(
        "/parse/",
        files=[
            ("files", ("s.pdf", generated_pdf_path.read_bytes(), "application/pdf"))
        ],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["term_context"]["term_id"] == "2026W"
    assert body["extraction"]["course_code"] == "CSC263H1S"
    assert body["events"][0]["date_confidence"] == "estimated"


def test_resolve_requires_auth(api_client: TestClient) -> None:
    resp = api_client.post("/parse/resolve", json={"extraction": _EXTRACTION})
    assert resp.status_code == 401


def test_resolve_applies_week1_override(authenticated_client: TestClient) -> None:
    base = authenticated_client.post(
        "/parse/resolve", json={"extraction": _EXTRACTION, "today": "2025-12-29"}
    )
    moved = authenticated_client.post(
        "/parse/resolve",
        json={
            "extraction": _EXTRACTION,
            "today": "2025-12-29",
            "override": {"week1_monday": "2026-01-12"},
        },
    )
    assert base.status_code == 200 and moved.status_code == 200
    d0 = base.json()["events"][0]["due_date"][:10]
    d1 = moved.json()["events"][0]["due_date"][:10]
    assert moved.json()["term_context"]["anchor_source"] == "user"
    assert d1 == "2026-01-26"
    assert d0 != d1


def test_resolve_rejects_bad_extraction(authenticated_client: TestClient) -> None:
    resp = authenticated_client.post("/parse/resolve", json={"extraction": {"nope": 1}})
    assert resp.status_code == 422


@patch("app.routers.parse.extract_text", new_callable=AsyncMock)
@patch("app.routers.parse.extract_syllabus", new_callable=AsyncMock)
def test_parse_fallback_returns_events_without_term_context(
    mock_extract: AsyncMock,
    mock_extract_text: AsyncMock,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    from app.services.llm import ExtractionOutcome

    mock_extract_text.return_value = "syllabus text"
    mock_extract.return_value = ExtractionOutcome(
        events=_mock_events(), term_context=None, extraction=None, raw=""
    )
    resp = authenticated_client.post(
        "/parse/",
        files=[
            ("files", ("s.pdf", generated_pdf_path.read_bytes(), "application/pdf"))
        ],
    )
    assert resp.status_code == 200
    assert resp.json()["term_context"] is None
    assert resp.json()["extraction"] is None
    assert len(resp.json()["events"]) == 1
