import hashlib


def target_hash(target: str) -> str:
    return hashlib.sha256(target.strip().lower().encode("utf-8")).hexdigest()
