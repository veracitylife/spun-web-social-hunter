import httpx


class BraveSearchClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def web_search(self, query: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Brave Search API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query},
            )
            response.raise_for_status()
            return response.json()


class SerpApiClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def search(self, query: str) -> dict:
        if not self.api_key:
            raise RuntimeError("SerpApi API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://serpapi.com/search.json",
                params={"q": query, "api_key": self.api_key},
            )
            response.raise_for_status()
            return response.json()
