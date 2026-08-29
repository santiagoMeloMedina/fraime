import httpx

from fraime.exceptions import FraimeAPIError, FraimeAuthError, FraimeConnectionError


class GenerationRepository:
    """Raw HTTP transport to the Fraime API — no model knowledge beyond JSON in/out."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 600.0):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def post_generate(self, payload: dict) -> dict:
        return self._request("POST", "/generate", json=payload)

    def get_models_config(self) -> dict:
        return self._request("GET", "/config/models")

    def get_rules_config(self) -> dict:
        return self._request("GET", "/config/rules")

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self._base_url}{path}"
        headers = {"Content-Type": "application/json"} if "json" in kwargs else {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            response = httpx.request(method, url, headers=headers, timeout=self._timeout, **kwargs)
        except httpx.RequestError as e:
            raise FraimeConnectionError(f"Failed to reach Fraime API at {url}: {e}") from e

        if response.status_code == 401:
            raise FraimeAuthError(response.text or "Invalid or missing API key")
        if response.status_code >= 400:
            raise FraimeAPIError(response.status_code, response.text)

        return response.json()
