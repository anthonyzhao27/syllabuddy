"""Supabase database helpers."""

from supabase import Client, ClientOptions, create_client

from app.config import settings


def get_authenticated_client(access_token: str) -> Client:
    """Create a request-scoped Supabase client with the user's JWT."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("Supabase credentials are not configured")

    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=ClientOptions(
            headers={"Authorization": f"Bearer {access_token}"},
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
