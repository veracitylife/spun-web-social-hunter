import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 210_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    candidate = hash_password(password, salt).split("$", 2)[2]
    return hmac.compare_digest(candidate, digest)


@dataclass
class UserAccount:
    username: str
    email: str
    role: str
    tenant_id: str
    plan: str
    password_hash: str
    active: bool = True
    failed_attempts: int = 0
    locked_until: str | None = None


@dataclass
class SessionContext:
    token: str
    username: str
    role: str
    tenant_id: str
    plan: str
    expires_at: str


_SESSIONS: dict[str, SessionContext] = {}


def default_users() -> list[UserAccount]:
    return [
        UserAccount(
            username="admin",
            email="admin@example.com",
            role="admin",
            tenant_id="platform",
            plan="operator",
            password_hash=hash_password("admin", "socialhunteradminsalt"),
        ),
        UserAccount(
            username="member",
            email="member@example.com",
            role="member",
            tenant_id="demo-tenant",
            plan="growth",
            password_hash=hash_password("member", "socialhuntermembersalt"),
        ),
    ]


def serialize_user(user: UserAccount) -> dict:
    data = asdict(user)
    data.pop("password_hash", None)
    return data


def login_user(users: list[UserAccount], username: str, password: str, required_role: str | None = None) -> SessionContext:
    lookup = username.strip().lower()
    user = next((item for item in users if item.username.lower() == lookup or item.email.lower() == lookup), None)
    if user is None or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if required_role and user.role != required_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not allowed for this gateway")
    if user.locked_until:
        locked_until = datetime.fromisoformat(user.locked_until)
        if locked_until > datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")
        user.locked_until = None
        user.failed_attempts = 0
    if not verify_password(password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.failed_attempts = 0
    user.locked_until = None
    token = secrets.token_urlsafe(32)
    session = SessionContext(
        token=token,
        username=user.username,
        role=user.role,
        tenant_id=user.tenant_id,
        plan=user.plan,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
    )
    _SESSIONS[token] = session
    return session


def require_session(authorization: str | None = Header(default=None)) -> SessionContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    session = _SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    if datetime.fromisoformat(session.expires_at) <= datetime.now(timezone.utc):
        _SESSIONS.pop(token, None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return session


def require_admin(authorization: str | None = Header(default=None)) -> SessionContext:
    session = require_session(authorization)
    if session.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return session
