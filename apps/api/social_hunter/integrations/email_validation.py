import httpx


class EmailValidationClient:
    def __init__(self, api_key: str | None, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def validate(self, email: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Email validation API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/validate",
                params={"email": email, "api_key": self.api_key},
            )
            response.raise_for_status()
            return response.json()
