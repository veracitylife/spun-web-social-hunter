import httpx


class ProviderNotConfigured(RuntimeError):
    pass


class HIBPClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def breached_account(self, email: str) -> list[dict]:
        if not self.api_key:
            raise ProviderNotConfigured("HIBP API key is not configured")
        headers = {"hibp-api-key": self.api_key, "user-agent": "SocialHunterEducational/0.1"}
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers, params={"truncateResponse": "false"})
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()
