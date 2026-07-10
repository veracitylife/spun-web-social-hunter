import httpx


class TwilioLookupClient:
    def __init__(self, account_sid: str | None, auth_token: str | None) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token

    async def lookup(self, phone_number: str, fields: str = "line_type_intelligence") -> dict:
        if not self.account_sid or not self.auth_token:
            raise RuntimeError("Twilio Lookup credentials are not configured")
        url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone_number}"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                url,
                params={"Fields": fields},
                auth=(self.account_sid, self.auth_token),
            )
            response.raise_for_status()
            return response.json()
