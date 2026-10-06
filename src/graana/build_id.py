"""Next.js ``buildId`` handling.

The detail endpoint is ``/_next/data/<buildId>/property/<idOrSlug>.json``. The
``buildId`` is fetched at the start of every run from the site's HTML (it is
embedded in ``__NEXT_DATA__``) and is never hardcoded. If a detail request 404s
because the site redeployed, the build id is refreshed exactly once and the
request retried.
"""

from __future__ import annotations

import re
import threading

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from graana.config import TransportConfig
from graana.http import HttpClient, RetryableHTTPError

_BUILD_ID_RE = re.compile(r'"buildId"\s*:\s*"([^"]+)"')


class BuildIdProvider:
    """Thread-safe, refreshable holder for the current Next.js build id."""

    def __init__(self, base_url: str, client: HttpClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._lock = threading.Lock()
        self._build_id: str | None = None

    @property
    def build_id(self) -> str:
        if self._build_id is None:
            self.refresh()
        assert self._build_id is not None
        return self._build_id

    def refresh(self) -> str:
        """Fetch a fresh build id from the site HTML."""
        with self._lock:
            self._build_id = self._fetch()
            return self._build_id

    @retry(
        retry=retry_if_exception_type(RetryableHTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _fetch(self) -> str:
        response = self._client.get(f"{self._base_url}/")
        match = _BUILD_ID_RE.search(response.text)
        if match is None:
            raise ValueError("buildId not found in site HTML")
        return match.group(1)


def detail_url(base_url: str, build_id: str, listing_id: int) -> str:
    """Return the detail JSON URL for a listing id.

    The endpoint resolves any slug suffix by id (it redirects to the canonical
    slug), so passing the bare id is sufficient.
    """
    return f"{base_url.rstrip('/')}/_next/data/{build_id}/property/{listing_id}.json"


def fetch_detail(
    client: HttpClient,
    provider: BuildIdProvider,
    base_url: str,
    listing_id: int,
) -> dict | None:
    """Fetch a listing's detail object, refreshing build id once on 404.

    The endpoint resolves the bare id to a canonical slug via an
    ``__N_REDIRECT`` payload, which is followed once. On a 404 (stale build id)
    the build id is refreshed exactly once and the request retried. Returns the
    raw ``pageProps.data`` dict, or ``None`` if the resource is unavailable.
    """
    data = _fetch_detail_once(client, provider, base_url, listing_id)
    if data is None:
        provider.refresh()
        data = _fetch_detail_once(client, provider, base_url, listing_id)
    return data


def _fetch_detail_once(
    client: HttpClient,
    provider: BuildIdProvider,
    base_url: str,
    listing_id: int,
) -> dict | None:
    url = detail_url(base_url, provider.build_id, listing_id)
    response = client.get(url, allow_404=True)
    if response.status_code == 404:
        return None
    page_props = response.json().get("pageProps") or {}
    data = page_props.get("data")
    if data is not None:
        return data
    # Follow the canonical-slug redirect once.
    redirect = page_props.get("__N_REDIRECT")
    if redirect:
        slug = str(redirect).rsplit("/", 1)[-1]
        redirect_url = detail_url(base_url, provider.build_id, slug)
        response = client.get(redirect_url, allow_404=True)
        if response.status_code == 404:
            return None
        return (response.json().get("pageProps") or {}).get("data")
    return None
