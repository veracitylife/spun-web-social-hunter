import httpx


class RdapClient:
    async def domain(self, domain: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"https://rdap.org/domain/{domain}")
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()


class SecurityTrailsClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def domain(self, domain: str) -> dict:
        if not self.api_key:
            raise RuntimeError("SecurityTrails API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.securitytrails.com/v1/domain/{domain}",
                headers={"APIKEY": self.api_key},
            )
            response.raise_for_status()
            return response.json()
