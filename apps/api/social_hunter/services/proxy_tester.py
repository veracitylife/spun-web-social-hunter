from __future__ import annotations

import asyncio
import ipaddress
import re
import time
from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote, urlparse, urlunparse

import httpx

from social_hunter.models import ProxyConnectionTestResponse, ProxyConnectionResult

PRIVATE_HOST_PATTERNS = ("localhost", "localhost.localdomain")


@dataclass(frozen=True)
class ParsedProxy:
    raw: str
    proxy_url: str | None
    redacted: str
    error: str | None = None


def _host_is_blocked(hostname: str | None) -> bool:
    if not hostname:
        return True
    host = hostname.strip().lower().strip("[]")
    if host in PRIVATE_HOST_PATTERNS or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved


def _target_allowed(target_url: str) -> tuple[bool, str]:
    parsed = urlparse(target_url)
    if parsed.scheme not in {"http", "https"}:
        return False, "Target URL must use http or https."
    if _host_is_blocked(parsed.hostname):
        return False, "Target URL cannot point at localhost, private, link-local, multicast, or reserved hosts."
    return True, ""


def _redact_url(proxy_url: str) -> str:
    parsed = urlparse(proxy_url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    if parsed.username:
        netloc = f"{parsed.username}:***@{netloc}"
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))


def _parse_proxy(entry: str) -> ParsedProxy:
    raw = entry.strip()
    if not raw:
        return ParsedProxy(raw=entry, proxy_url=None, redacted="", error="empty proxy entry")

    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            return ParsedProxy(raw=raw, proxy_url=None, redacted=_redact_url(raw), error=f"unsupported proxy scheme: {parsed.scheme}")
        if not parsed.hostname or not parsed.port:
            return ParsedProxy(raw=raw, proxy_url=None, redacted=_redact_url(raw), error="proxy URL must include host and port")
        return ParsedProxy(raw=raw, proxy_url=raw, redacted=_redact_url(raw))

    parts = raw.split(":")
    if len(parts) == 2:
        host, port = parts
        proxy_url = f"http://{host}:{port}"
        return ParsedProxy(raw=raw, proxy_url=proxy_url, redacted=f"http://{host}:{port}")
    if len(parts) >= 4:
        host, port, username = parts[0], parts[1], parts[2]
        password = ":".join(parts[3:])
        proxy_url = f"http://{quote(username)}:{quote(password)}@{host}:{port}"
        return ParsedProxy(raw=raw, proxy_url=proxy_url, redacted=f"http://{username}:***@{host}:{port}")
    return ParsedProxy(raw=raw, proxy_url=None, redacted="invalid entry", error="use host:port, host:port:user:pass, or http(s)://user:pass@host:port")


def _safe_error(exc: Exception, parsed: ParsedProxy) -> str:
    text = f"{exc.__class__.__name__}: {str(exc)[:180]}"
    if parsed.raw:
        text = text.replace(parsed.raw, "[proxy]")
    if parsed.proxy_url:
        text = text.replace(parsed.proxy_url, "[proxy]")
    return text


async def _test_one(index: int, entry: str, target_url: str, timeout_seconds: float) -> ProxyConnectionResult:
    parsed = _parse_proxy(entry)
    if parsed.error or not parsed.proxy_url:
        return ProxyConnectionResult(index=index, proxy=parsed.redacted or f"entry {index + 1}", ok=False, status="invalid_format", error=parsed.error or "invalid proxy entry", target_url=target_url)

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(proxy=parsed.proxy_url, timeout=timeout_seconds, follow_redirects=True, trust_env=False) as client:
            response = await client.get(target_url, headers={"User-Agent": "SocialHunterProxyTest/1.0"})
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        ok = 200 <= response.status_code < 400
        return ProxyConnectionResult(
            index=index,
            proxy=parsed.redacted,
            ok=ok,
            status="connected" if ok else "failed",
            latency_ms=latency_ms,
            http_status=response.status_code,
            error="" if ok else f"Target returned HTTP {response.status_code}",
            target_url=target_url,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return ProxyConnectionResult(index=index, proxy=parsed.redacted, ok=False, status="failed", latency_ms=latency_ms, error=_safe_error(exc, parsed), target_url=target_url)


async def test_proxy_connections(entries: list[str], target_url: str, timeout_seconds: float = 8, concurrency: int = 4) -> ProxyConnectionTestResponse:
    cleaned = [entry.strip() for entry in entries if entry.strip()]
    allowed, reason = _target_allowed(target_url)
    if not allowed:
        return ProxyConnectionTestResponse(ok=False, tested=0, connected=0, failed=len(cleaned), target_url=target_url, results=[ProxyConnectionResult(index=i, proxy=f"entry {i + 1}", ok=False, status="skipped", error=reason, target_url=target_url) for i, _ in enumerate(cleaned)], message=reason)

    limited = cleaned[:200]
    semaphore = asyncio.Semaphore(max(1, min(concurrency, 10)))

    async def bounded(index: int, entry: str) -> ProxyConnectionResult:
        async with semaphore:
            return await _test_one(index, entry, target_url, timeout_seconds)

    results = await asyncio.gather(*(bounded(index, entry) for index, entry in enumerate(limited)))
    connected = sum(1 for item in results if item.ok)
    failed = len(results) - connected
    return ProxyConnectionTestResponse(ok=failed == 0 and len(results) > 0, tested=len(results), connected=connected, failed=failed, target_url=target_url, results=results, message=f"Proxy connection test complete: {connected}/{len(results)} connected.")
