"""Endpoint tests for files router behavior."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def _syllabus_row(syllabus_id: str = "syllabus-1") -> dict[str, object]:
    return {
        "id": syllabus_id,
        "name": "CSC413 Winter 2025",
        "course_code": "CSC413",
        "source_type": "file",
        "original_filename": "syllabus.pdf",
        "storage_paths": [f"00000000-0000-0000-0000-000000000001/{syllabus_id}.pdf"],
        "created_at": "2025-01-01T12:00:00+00:00",
    }


def _event_row(event_id: str = "event-1") -> dict[str, object]:
    return {
        "id": event_id,
        "title": "Homework 1",
        "due_date": "2025-01-30T15:00:00+00:00",
        "course": "CSC413",
        "event_type": "assignment",
        "description": "",
        "time_specified": True,
        "duration_minutes": None,
        "is_edited": False,
    }


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/files/", None),
        ("get", "/files/syllabus-1", None),
        ("get", "/files/syllabus-1/download", None),
        ("delete", "/files/syllabus-1", None),
        ("patch", "/files/syllabus-1/events/event-1", {"title": "Updated"}),
        ("delete", "/files/syllabus-1/events/event-1", None),
    ],
)
def test_files_endpoints_require_auth(
    api_client: TestClient,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    response = api_client.request(method.upper(), path, json=payload)
    assert response.status_code == 401


@patch("app.routers.files.syllabi_service.list_syllabi", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.get_event_counts_for_syllabi",
    new_callable=AsyncMock,
)
def test_list_user_syllabi(
    mock_counts: AsyncMock,
    mock_list_syllabi: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_list_syllabi.return_value = [
        _syllabus_row("syllabus-1"),
        _syllabus_row("syllabus-2"),
    ]
    mock_counts.return_value = {"syllabus-1": 3, "syllabus-2": 1}

    response = authenticated_client.get("/files/")

    assert response.status_code == 200
    assert response.json()["syllabi"][0]["event_count"] == 3
    assert response.json()["syllabi"][1]["event_count"] == 1


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.get_events_for_syllabus",
    new_callable=AsyncMock,
)
def test_get_syllabus_detail(
    mock_get_events: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_syllabus.return_value = _syllabus_row()
    mock_get_events.return_value = [_event_row()]

    response = authenticated_client.get("/files/syllabus-1")

    assert response.status_code == 200
    assert response.json()["syllabus"]["id"] == "syllabus-1"
    assert response.json()["events"][0]["id"] == "event-1"


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.delete_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.storage_service.delete_file_best_effort",
    new_callable=AsyncMock,
)
def test_delete_syllabus(
    mock_delete_file: AsyncMock,
    mock_delete_syllabus: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    syllabus = _syllabus_row()
    syllabus["storage_paths"] = ["user/file1.pdf", "user/file2.pdf"]
    mock_get_syllabus.return_value = syllabus
    mock_delete_syllabus.return_value = True

    response = authenticated_client.delete("/files/syllabus-1")

    assert response.status_code == 200
    assert response.json()["message"] == "Syllabus deleted"
    assert mock_delete_file.await_count == 2


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch("app.routers.files.storage_service.download_file", new_callable=AsyncMock)
def test_download_single_file(
    mock_download_file: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_syllabus.return_value = _syllabus_row()
    mock_download_file.return_value = b"pdf-bytes"

    response = authenticated_client.get("/files/syllabus-1/download")

    assert response.status_code == 200
    assert response.content == b"pdf-bytes"
    assert 'filename="syllabus.pdf"' in response.headers["content-disposition"]


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.storage_service.download_files_as_zip",
    new_callable=AsyncMock,
)
def test_download_multiple_files_as_zip(
    mock_download_zip: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    syllabus = _syllabus_row()
    syllabus["storage_paths"] = ["user/file1.png", "user/file2.png"]
    syllabus["source_type"] = "screenshots"
    syllabus["original_filename"] = None
    mock_get_syllabus.return_value = syllabus
    mock_download_zip.return_value = b"zip-bytes"

    response = authenticated_client.get("/files/syllabus-1/download")

    assert response.status_code == 200
    assert response.content == b"zip-bytes"
    assert response.headers["content-type"] == "application/zip"
    assert (
        'filename="CSC413 Winter 2025.zip"' in response.headers["content-disposition"]
    )


@patch("app.routers.files.syllabi_service.get_event", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.update_event", new_callable=AsyncMock)
def test_update_event_preserves_existing_time_for_date_only_edit(
    mock_update_event: AsyncMock,
    mock_get_event: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_event.return_value = _event_row()
    updated_event = _event_row()
    updated_event["due_date"] = "2025-02-01T15:00:00+00:00"
    updated_event["is_edited"] = True
    mock_update_event.return_value = updated_event

    response = authenticated_client.patch(
        "/files/syllabus-1/events/event-1",
        json={"due_date": "2025-02-01"},
    )

    assert response.status_code == 200
    update_data = mock_update_event.await_args.args[3]
    assert update_data["due_date"] == "2025-02-01T15:00:00+00:00"
    assert update_data["time_specified"] is True


@patch("app.routers.files.syllabi_service.get_event", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.update_event", new_callable=AsyncMock)
def test_update_event_clears_time_when_requested(
    mock_update_event: AsyncMock,
    mock_get_event: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_event.return_value = _event_row()
    updated_event = _event_row()
    updated_event["due_date"] = "2025-02-01T23:59:00"
    updated_event["time_specified"] = False
    updated_event["is_edited"] = True
    mock_update_event.return_value = updated_event

    response = authenticated_client.patch(
        "/files/syllabus-1/events/event-1",
        json={"due_date": "2025-02-01", "time_specified": False},
    )

    assert response.status_code == 200
    update_data = mock_update_event.await_args.args[3]
    assert update_data["due_date"] == "2025-02-01T23:59:00"
    assert update_data["time_specified"] is False


@patch("app.routers.files.syllabi_service.get_event", new_callable=AsyncMock)
def test_update_event_rejects_ambiguous_date_with_time_specified_true(
    mock_get_event: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_event.return_value = _event_row()

    response = authenticated_client.patch(
        "/files/syllabus-1/events/event-1",
        json={"due_date": "2025-02-01", "time_specified": True},
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "time_specified=true requires a full datetime value for due_date"
    )


@patch("app.routers.files.syllabi_service.get_event", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.update_event", new_callable=AsyncMock)
def test_update_event_returns_404_when_row_disappears_during_update(
    mock_update_event: AsyncMock,
    mock_get_event: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_event.return_value = _event_row()
    mock_update_event.return_value = None

    response = authenticated_client.patch(
        "/files/syllabus-1/events/event-1",
        json={"title": "Updated title"},
    )

    assert response.status_code == 404


@patch("app.routers.files.syllabi_service.soft_delete_event", new_callable=AsyncMock)
def test_delete_event(
    mock_soft_delete: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_soft_delete.return_value = True

    response = authenticated_client.delete("/files/syllabus-1/events/event-1")

    assert response.status_code == 200
    assert response.json()["message"] == "Event deleted"


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
        },
        {
            "title": "Quiz 1",
            "event_type": "quiz",
            "description": "",
            "date_kind": "week",
            "date": None,
            "stated_weekday": None,
            "week": 4,
            "in_class": False,
            "meeting_kind": None,
            "time": None,
            "duration_minutes": None,
            "source_text": "Week 4: quiz 1",
        },
    ],
    "recurring": [],
}


def _term_context() -> dict:
    from datetime import date

    from app.models.schemas import LLMSyllabus
    from app.services.llm import resolve_extraction

    _, ctx = resolve_extraction(
        LLMSyllabus.model_validate(_EXTRACTION), date(2025, 12, 29)
    )
    return ctx.model_dump(mode="json")


@patch("app.routers.files.syllabi_service.get_event", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.update_event", new_callable=AsyncMock)
def test_update_event_date_clears_confidence(
    mock_update_event: AsyncMock,
    mock_get_event: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_event.return_value = _event_row()
    mock_update_event.return_value = {**_event_row(), "is_edited": True}

    response = authenticated_client.patch(
        "/files/syllabus-1/events/event-1", json={"due_date": "2025-02-01"}
    )

    assert response.status_code == 200
    update_data = mock_update_event.await_args.args[3]
    assert update_data["date_confidence"] is None
    assert update_data["date_source"] == ""


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.get_events_for_syllabus",
    new_callable=AsyncMock,
)
def test_detail_exposes_term_context_and_confidence(
    mock_get_events: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_syllabus.return_value = {
        **_syllabus_row(),
        "term_context": _term_context(),
        "extraction": _EXTRACTION,
    }
    mock_get_events.return_value = [
        {**_event_row(), "date_confidence": "inferred", "date_source": "Week 3"}
    ]

    body = authenticated_client.get("/files/syllabus-1").json()

    assert body["syllabus"]["term_context"]["term_id"] == "2026W"
    assert body["syllabus"]["can_redate"] is True
    assert body["events"][0]["date_confidence"] == "inferred"


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
def test_resolve_saved_requires_stored_extraction(
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    mock_get_syllabus.return_value = _syllabus_row()
    response = authenticated_client.post("/files/syllabus-1/resolve", json={})
    assert response.status_code == 409


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.get_events_for_syllabus",
    new_callable=AsyncMock,
)
@patch("app.routers.files.syllabi_service.save_events", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.delete_events", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.update_syllabus_term_context",
    new_callable=AsyncMock,
)
@patch(
    "app.routers.files.syllabi_service.get_deleted_events",
    new_callable=AsyncMock,
    return_value=[{"title": "Quiz 1", "source_key": "e1"}],
)
def test_resolve_saved_keeps_edited_and_replaces_rest(
    mock_deleted: AsyncMock,
    mock_update_ctx: AsyncMock,
    mock_soft_delete: AsyncMock,
    mock_save: AsyncMock,
    mock_get_events: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    row = {
        **_syllabus_row(),
        "parsed_at": "2025-12-29T12:00:00+00:00",
        "term_context": _term_context(),
        "extraction": _EXTRACTION,
    }
    mock_get_syllabus.return_value = row
    mock_update_ctx.return_value = row
    edited = {
        **_event_row("e-edited"),
        "title": "Midterm",
        "is_edited": True,
        "source_key": "e9",
    }
    stale = {**_event_row("e-stale"), "title": "Essay", "source_key": "e0"}
    mock_get_events.side_effect = [[edited, stale], [edited]]

    response = authenticated_client.post(
        "/files/syllabus-1/resolve",
        json={"override": {"week1_monday": "2026-01-12"}},
    )

    assert response.status_code == 200
    saved = mock_save.await_args.args[3]
    assert [e.title for e in saved] == ["Essay"]
    # week 3 with week 1 = Jan 12 -> Monday Jan 26
    assert saved[0].due_date.date().isoformat() == "2026-01-26"
    assert mock_soft_delete.await_args.args[2] == ["e-stale"]
    assert mock_update_ctx.await_args.args[2]["anchor_source"] == "user"


@pytest.mark.parametrize("valid", [True, False])
@patch("app.routers.files.classify_upload", new_callable=AsyncMock)
@patch("app.routers.files.storage_service.upload_files", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.create_syllabus", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.save_events", new_callable=AsyncMock)
def test_save_persists_term_context_and_extraction(
    mock_save_events: AsyncMock,
    mock_create: AsyncMock,
    mock_upload: AsyncMock,
    mock_classify: AsyncMock,
    valid: bool,
    authenticated_client: TestClient,
    generated_pdf_path,
) -> None:
    import json

    mock_classify.return_value = "application/pdf"
    mock_upload.return_value = {"paths": ["u/s.pdf"], "total_size": 10}
    mock_create.return_value = {"id": "syllabus-1"}
    events = [
        {
            "title": "Essay",
            "due_date": "2026-01-19T23:59:00",
            "course": "CSC263H1S",
            "event_type": "assignment",
            "description": "",
            "time_specified": False,
            "duration_minutes": None,
            "date_confidence": "estimated",
            "date_source": "Week 3 → Monday (no day given)",
        }
    ]
    response = authenticated_client.post(
        "/files/",
        files=[
            ("files", ("s.pdf", generated_pdf_path.read_bytes(), "application/pdf"))
        ],
        data={
            "events_json": json.dumps(events),
            "term_context_json": json.dumps(_term_context()) if valid else "{bad",
            "extraction_json": json.dumps(_EXTRACTION),
        },
    )

    assert response.status_code == 200
    kwargs = mock_create.await_args.kwargs
    if valid:
        assert kwargs["term_context"]["term_id"] == "2026W"
        assert kwargs["extraction"]["course_code"] == "CSC263H1S"
    else:
        assert kwargs["term_context"] is None and kwargs["extraction"] is None
    saved = mock_save_events.await_args.args[3]
    assert saved[0].date_confidence == "estimated"


@patch("app.routers.files.syllabi_service.get_syllabus", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.get_events_for_syllabus",
    new_callable=AsyncMock,
)
@patch("app.routers.files.syllabi_service.save_events", new_callable=AsyncMock)
@patch("app.routers.files.syllabi_service.delete_events", new_callable=AsyncMock)
@patch(
    "app.routers.files.syllabi_service.update_syllabus_term_context",
    new_callable=AsyncMock,
)
@patch("app.routers.files.syllabi_service.get_deleted_events", new_callable=AsyncMock)
def test_resolve_saved_deleting_one_recurring_instance_keeps_the_rest(
    mock_deleted: AsyncMock,
    mock_update_ctx: AsyncMock,
    mock_delete: AsyncMock,
    mock_save: AsyncMock,
    mock_get_events: AsyncMock,
    mock_get_syllabus: AsyncMock,
    authenticated_client: TestClient,
) -> None:
    extraction = {
        **_EXTRACTION,
        "events": [],
        "recurring": [
            {
                "title": "Weekly Quiz",
                "event_type": "quiz",
                "description": "",
                "weekday": "friday",
                "in_class": False,
                "meeting_kind": None,
                "time": None,
                "weeks": [2, 3, 4],
                "first_date": None,
                "last_date": None,
                "every_n_weeks": 1,
                "excluded_weeks": [],
                "duration_minutes": None,
                "source_text": "quiz every Friday, weeks 2-4",
            }
        ],
    }
    row = {
        **_syllabus_row(),
        "parsed_at": "2025-12-29T12:00:00+00:00",
        "term_context": _term_context(),
        "extraction": extraction,
    }
    mock_get_syllabus.return_value = row
    mock_update_ctx.return_value = row
    mock_deleted.return_value = [{"title": "Weekly Quiz", "source_key": "r0:1"}]
    mock_get_events.side_effect = [[], []]

    response = authenticated_client.post("/files/syllabus-1/resolve", json={})

    assert response.status_code == 200
    saved = mock_save.await_args.args[3]
    assert [e.source_key for e in saved] == ["r0:0", "r0:2"]
