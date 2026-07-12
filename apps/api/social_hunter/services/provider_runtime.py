from time import perf_counter

from social_hunter.connectors.search import web_search_index_lookup
from social_hunter.connectors.username import github_user_lookup
from social_hunter.models import ProviderRuntimeTestResponse
from social_hunter.services.vault import vault_reference_available


async def test_provider_runtime(provider_id: str, sample_target: str) -> ProviderRuntimeTestResponse:
    start = perf_counter()
    try:
        if provider_id == "github-users":
            findings = await github_user_lookup(sample_target or "octocat")
            ok = any(f.status == "found" for f in findings)
            return ProviderRuntimeTestResponse(
                provider_id=provider_id,
                ok=ok,
                status="ready" if ok else "error",
                message="GitHub public Users API returned normalized findings." if ok else "GitHub lookup did not return a found profile.",
                latency_ms=round((perf_counter() - start) * 1000, 2),
                finding_count=len(findings),
            )
        if provider_id == "web-search-indexes":
            if not vault_reference_available("BRAVE_SEARCH_API_KEY_REF") and not vault_reference_available("BRAVE_SEARCH_API_KEY_"):
                return ProviderRuntimeTestResponse(
                    provider_id=provider_id,
                    ok=False,
                    status="needs_key",
                    message="Brave Search key reference is configured but not available in this runtime environment.",
                    latency_ms=round((perf_counter() - start) * 1000, 2),
                )
            findings = await web_search_index_lookup(sample_target or "Social Hunter")
            ok = any(f.status == "found" for f in findings)
            return ProviderRuntimeTestResponse(
                provider_id=provider_id,
                ok=ok,
                status="ready" if ok else "error",
                message="Brave Search API returned normalized findings." if ok else findings[0].evidence if findings else "No findings returned.",
                latency_ms=round((perf_counter() - start) * 1000, 2),
                finding_count=len(findings),
            )
        return ProviderRuntimeTestResponse(
            provider_id=provider_id,
            ok=False,
            status="skipped",
            message="Runtime live test is not implemented for this provider yet; reference validation is available.",
            latency_ms=round((perf_counter() - start) * 1000, 2),
        )
    except Exception as exc:
        return ProviderRuntimeTestResponse(
            provider_id=provider_id,
            ok=False,
            status="error",
            message=f"Provider runtime test failed: {exc.__class__.__name__}",
            latency_ms=round((perf_counter() - start) * 1000, 2),
        )
