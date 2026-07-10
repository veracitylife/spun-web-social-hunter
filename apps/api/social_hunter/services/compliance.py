"""Compliance and target denylisting service for protected classes and regulatory restrictions."""
import hashlib
import re
from typing import Optional

from pydantic import BaseModel, Field


class ComplianceConfig(BaseModel):
    """Compliance and denylisting configuration."""
    # Email patterns to block (e.g., minors, protected organizations)
    blocked_email_patterns: list[str] = Field(
        default_factory=lambda: [
            r".*@schools\.gov$",  # Public school domains
            r".*@k12\..*",  # K-12 schools
            r".*@nhs\.uk$",  # UK NHS
            r".*@medicaid\.gov$",  # US Medicaid
        ]
    )
    blocked_username_patterns: list[str] = Field(
        default_factory=lambda: [
            r"^(child|kid|baby|teen)_.*",  # Obvious minor indicators
            r".*_under_?18$",
        ]
    )
    blocked_domains: list[str] = Field(
        default_factory=lambda: [
            "internal.company.local",  # Internal-only domains (add as needed)
            "127.0.0.1",
            "localhost",
        ]
    )
    blocked_ips: list[str] = Field(
        default_factory=lambda: [
            "127.0.0.1",
            "::1",
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12",
        ]
    )


class ComplianceCheckResult(BaseModel):
    """Result of a compliance check."""
    allowed: bool
    reason: Optional[str] = None  # Reason if denied
    flags: list[str] = Field(default_factory=list)  # Warning flags even if allowed


class ComplianceService:
    """Enforces compliance rules: blocks protected classes, minors, internal targets."""

    def __init__(self, config: ComplianceConfig):
        self.config = config
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self.blocked_email_patterns_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.config.blocked_email_patterns
        ]
        self.blocked_username_patterns_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.config.blocked_username_patterns
        ]

    async def check_compliance(self, target_type: str, target: str) -> ComplianceCheckResult:
        """
        Check if a target passes compliance rules.
        Returns ComplianceCheckResult with allowed flag and reasons.
        """
        if target_type == "email":
            return await self._check_email_compliance(target)
        elif target_type == "username":
            return await self._check_username_compliance(target)
        elif target_type == "domain":
            return await self._check_domain_compliance(target)
        elif target_type == "ip":
            return await self._check_ip_compliance(target)
        return ComplianceCheckResult(allowed=True)

    async def _check_email_compliance(self, email: str) -> ComplianceCheckResult:
        """Check email against denylists and patterns."""
        email_lower = email.lower()

        # Check exact blocklist
        if email_lower in self.config.blocked_email_patterns:
            return ComplianceCheckResult(
                allowed=False,
                reason=f"Email '{email}' is on the compliance blocklist.",
            )

        # Check pattern blocklist
        for pattern in self.blocked_email_patterns_compiled:
            if pattern.search(email_lower):
                return ComplianceCheckResult(
                    allowed=False,
                    reason=f"Email domain matches blocked pattern: {pattern.pattern}",
                )

        return ComplianceCheckResult(allowed=True)

    async def _check_username_compliance(self, username: str) -> ComplianceCheckResult:
        """Check username against blocklists and minor indicators."""
        username_lower = username.lower()

        # Check pattern blocklist (minor indicators)
        for pattern in self.blocked_username_patterns_compiled:
            if pattern.search(username_lower):
                return ComplianceCheckResult(
                    allowed=False,
                    reason=f"Username pattern suggests potential minor: {pattern.pattern}",
                )

        return ComplianceCheckResult(allowed=True)

    async def _check_domain_compliance(self, domain: str) -> ComplianceCheckResult:
        """Check domain against blocklists and internal domain patterns."""
        domain_lower = domain.lower()

        # Check exact blocklist
        if domain_lower in self.config.blocked_domains:
            return ComplianceCheckResult(
                allowed=False,
                reason=f"Domain '{domain}' is blocked (internal-only or reserved).",
            )

        # Check for local/internal domains
        if domain_lower in ["localhost", "127.0.0.1"] or domain_lower.endswith(".local"):
            return ComplianceCheckResult(
                allowed=False,
                reason="Domain is internal/local and cannot be searched.",
            )

        return ComplianceCheckResult(allowed=True)

    async def _check_ip_compliance(self, ip: str) -> ComplianceCheckResult:
        """Check IP against blocklists and private ranges."""
        # Check exact blocklist
        if ip in self.config.blocked_ips:
            return ComplianceCheckResult(
                allowed=False,
                reason=f"IP address '{ip}' is blocked.",
            )

        # Check private/reserved ranges
        if self._is_private_ip(ip):
            return ComplianceCheckResult(
                allowed=False,
                reason="Private IP addresses cannot be searched.",
            )

        return ComplianceCheckResult(allowed=True)

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Check if IP is in private/reserved ranges."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private or addr.is_loopback or addr.is_reserved
        except ValueError:
            return False
