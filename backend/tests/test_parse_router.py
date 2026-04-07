"""Integration tests for the /parse endpoint."""

import struct
import zlib
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.schemas import ParsedEvent


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
    assert resp.json()["detail"] == "When uploading screenshots, all files must be images."
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
