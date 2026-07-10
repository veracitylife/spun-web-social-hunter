import httpx


class PeopleDataLabsClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def person_enrichment(self, **params: str) -> dict:
        if not self.api_key:
            raise RuntimeError("People Data Labs API key is not configured")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                "https://api.peopledatalabs.com/v5/person/enrich",
                headers={"X-Api-Key": self.api_key},
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def company_enrichment(self, **params: str) -> dict:
        if not self.api_key:
            raise RuntimeError("People Data Labs API key is not configured")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                "https://api.peopledatalabs.com/v5/company/enrich",
                headers={"X-Api-Key": self.api_key},
                params=params,
            )
            response.raise_for_status()
            return response.json()
