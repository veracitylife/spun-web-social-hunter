import httpx


class GitHubUsersClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token

    async def user(self, username: str) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"https://api.github.com/users/{username}", headers=headers)
            if response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()


class XUsersClient:
    def __init__(self, bearer_token: str | None) -> None:
        self.bearer_token = bearer_token

    async def user_by_username(self, username: str) -> dict:
        if not self.bearer_token:
            raise RuntimeError("X bearer token is not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"https://api.x.com/2/users/by/username/{username}",
                headers={"Authorization": f"Bearer {self.bearer_token}"},
                params={"user.fields": "description,entities,location,public_metrics,verified"},
            )
            response.raise_for_status()
            return response.json()
