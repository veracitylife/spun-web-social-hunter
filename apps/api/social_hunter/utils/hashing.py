"""Hashing utilities for privacy."""
import hashlib


def hash_target(target: str) -> str:
    """Create SHA-256 hash of target for privacy."""
    return hashlib.sha256(target.encode()).hexdigest()
