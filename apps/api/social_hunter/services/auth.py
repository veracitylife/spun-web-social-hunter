from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContext:
    actor_id: str
    organization_id: str
    role: str


def demo_auth_context() -> AuthContext:
    return AuthContext(actor_id="demo-analyst", organization_id="demo-org", role="owner")
