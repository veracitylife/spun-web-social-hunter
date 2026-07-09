from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    monthly_search_limit: int
    export_enabled: bool
    api_access_enabled: bool


PLANS = [
    Plan(id="education", name="Education", monthly_search_limit=500, export_enabled=True, api_access_enabled=False),
    Plan(id="analyst", name="Analyst", monthly_search_limit=5000, export_enabled=True, api_access_enabled=True),
    Plan(id="team", name="Team", monthly_search_limit=25000, export_enabled=True, api_access_enabled=True),
]
