import httpx


class IPinfoClient:
    def __init__(self, token: str | None) -> None:
        self.token = token

    async def lookup(self, ip: str) -> dict:
        if not self.token:
            raise RuntimeError("IPinfo token is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://ipinfo.io/{ip}/json", params={"token": self.token})
            response.raise_for_status()
            return response.json()
