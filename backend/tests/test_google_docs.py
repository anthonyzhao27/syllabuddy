"""Tests for Google Docs fetching service."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.google_docs import _parse_doc_id, fetch_google_doc


def test_parse_doc_id_valid() -> None:
    url = "https://docs.google.com/document/d/1aBcDeFgHiJk/edit"
    assert _parse_doc_id(url) == "1aBcDeFgHiJk"


def test_parse_doc_id_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        _parse_doc_id("https://example.com/not-a-doc")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_fetch_google_doc_success() -> None:
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.text = "Homework 1 due Jan 30"

    with patch("app.services.google_docs.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get = AsyncMock(return_value=mock_resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        text = await fetch_google_doc("https://docs.google.com/document/d/abc123/edit")
        assert "Homework 1" in text


@pytest.mark.asyncio
async def test_fetch_google_doc_not_shared() -> None:
    mock_resp = AsyncMock()
    mock_resp.status_code = 403
    mock_resp.text = ""

    with patch("app.services.google_docs.httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.get = AsyncMock(return_value=mock_resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = instance

        with pytest.raises(HTTPException) as exc:
            await fetch_google_doc("https://docs.google.com/document/d/abc123/edit")
        assert exc.value.status_code == 502
