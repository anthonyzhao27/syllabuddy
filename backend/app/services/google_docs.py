"""Fetch Google Docs content via export URL."""

import re

import httpx
from fastapi import HTTPException

_DOC_ID_PATTERN = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")


def _parse_doc_id(url: str) -> str:
    """Extract the document ID from a Google Docs URL."""
    match = _DOC_ID_PATTERN.search(url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Google Docs URL.")
    return match.group(1)


async def fetch_google_doc(doc_url: str) -> str:
    """Download a public Google Doc as plain text."""
    doc_id = _parse_doc_id(doc_url)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(export_url)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch Google Doc (status {resp.status_code}). Is the doc publicly shared?",
        )

    text = resp.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Google Doc appears to be empty.")

    return text
