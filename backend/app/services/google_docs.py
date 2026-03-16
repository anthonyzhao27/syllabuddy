"""Fetch Google Docs content via export URL."""

import httpx


async def fetch_google_doc(doc_url: str) -> str:
    """Download a Google Doc as plain text using its export URL."""
    # TODO: parse doc ID from URL, build export URL, fetch content
    raise NotImplementedError("Google Docs fetching not yet implemented")
