import httpx

from fraime.exceptions import FraimeAPIError, FraimeAuthError, FraimeConnectionError


class GenerationRepository:
    """Raw HTTP transport to the Fraime API — no model knowledge beyond JSON in/out."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 600.0):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def post_generate(self, payload: dict) -> dict:
        url = f"{self._base_url}/generate"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=self._timeout)
        except httpx.RequestError as e:
            raise FraimeConnectionError(f"Failed to reach Fraime API at {url}: {e}") from e

        if response.status_code == 401:
            raise FraimeAuthError(response.text or "Invalid or missing API key")
        if response.status_code >= 400:
            raise FraimeAPIError(response.status_code, response.text)

        return response.json()
