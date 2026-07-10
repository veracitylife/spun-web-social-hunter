import httpx


class HunterClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def domain_search(self, domain: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Hunter.io API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": self.api_key},
            )
            response.raise_for_status()
            return response.json()

    async def email_verifier(self, email: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Hunter.io API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": self.api_key},
            )
            response.raise_for_status()
            return response.json()
