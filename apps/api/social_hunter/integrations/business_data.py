import httpx


class GooglePlacesClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def text_search(self, query: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Google Places API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": query, "key": self.api_key},
            )
            response.raise_for_status()
            return response.json()


class YelpFusionClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def business_search(self, term: str, location: str) -> dict:
        if not self.api_key:
            raise RuntimeError("Yelp Fusion API key is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://api.yelp.com/v3/businesses/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"term": term, "location": location},
            )
            response.raise_for_status()
            return response.json()
