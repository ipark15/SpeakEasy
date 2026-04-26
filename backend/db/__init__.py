import os
import httpx
from supabase import create_client, Client
from supabase.client import ClientOptions

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"].rstrip("/")
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(
            url, key,
            options=ClientOptions(httpx_client=httpx.Client(http2=False)),
        )
    return _client
