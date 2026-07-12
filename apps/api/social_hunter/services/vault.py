import json
import os
from pathlib import Path


def candidate_env_names(vault_reference: str) -> list[str]:
    ref = vault_reference.strip()
    if not ref or ref == "REPLACE_WITH_VAULT_REFERENCE":
        return []
    names = [ref]
    if ref.startswith("VAULT_REF_"):
        names.append(ref.removeprefix("VAULT_REF_"))
    if ref.endswith("_REF"):
        names.append(ref.removesuffix("_REF"))
    if ref.startswith("VAULT_REF_") and ref.endswith("_REF"):
        names.append(ref.removeprefix("VAULT_REF_").removesuffix("_REF"))
    names.extend([name + "_" for name in list(names) if not name.endswith("_")])
    seen: list[str] = []
    for name in names:
        clean = name.strip().upper().replace("-", "_")
        if clean and clean not in seen:
            seen.append(clean)
    return seen


def resolve_vault_reference(vault_reference: str) -> str | None:
    for env_name in candidate_env_names(vault_reference):
        value = os.getenv(env_name)
        if value:
            return value
    return None


def vault_reference_available(vault_reference: str) -> bool:
    return resolve_vault_reference(vault_reference) is not None


def redacted_reference_status(vault_reference: str) -> dict[str, str | bool]:
    names = candidate_env_names(vault_reference)
    return {
        "vault_reference": vault_reference,
        "mapped_env_names": ",".join(names),
        "available": any(os.getenv(name) for name in names),
    }
