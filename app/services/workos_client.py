"""
The one seam between this app and WorkOS.

A single module-level singleton, kept behind a function rather than called
inline, so tests can monkeypatch this one spot instead of reaching into the
SDK's own HTTP client internals.
"""

from typing import Optional

from workos import AsyncWorkOSClient

_client: Optional[AsyncWorkOSClient] = None


def get_workos_client() -> AsyncWorkOSClient:
    global _client
    if _client is None:
        from ..utils.config import settings

        _client = AsyncWorkOSClient(
            api_key=settings.WORKOS_API_KEY,
            client_id=settings.WORKOS_CLIENT_ID,
        )
    return _client
