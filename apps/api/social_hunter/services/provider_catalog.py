from importlib import import_module

from social_hunter.models import ApiKeyReference, ProviderConfig, ProxyRouteRule
from social_hunter.sources import SOURCE_CAPABILITIES



_PROVIDER_META: dict[str, dict[str, object]] = {
    "whatsmyname-import": {
        "function": "connectors.username.username_lookup",
        "credential_refs": [],
        "admin_section": "username_profile",
        "proxy_route": False,
        "note": "Local dataset import for public username-profile URL generation.",
    },
    "github-users": {
        "function": "connectors.username.github_user_lookup",
        "credential_refs": ["GITHUB_TOKEN_REF"],
        "admin_section": "username_profile",
        "proxy_route": False,
        "note": "Public GitHub user profile lookup; token is optional for higher API limits.",
    },
    "reddit-api": {
        "function": "connectors.username.reddit_profile_lookup",
        "credential_refs": ["REDDIT_CLIENT_ID_REF", "REDDIT_CLIENT_SECRET_REF"],
        "admin_section": "username_profile",
        "proxy_route": False,
        "note": "Public Reddit profile metadata through approved Reddit API access.",
    },
    "x-user-lookup": {
        "function": "connectors.username.x_user_lookup",
        "credential_refs": ["X_BEARER_TOKEN_REF"],
        "admin_section": "username_profile",
        "proxy_route": False,
        "note": "X username metadata through approved X API tier.",
    },
    "public-profile-sources": {
        "function": "connectors.username.public_profile_source_lookup",
        "credential_refs": [],
        "admin_section": "username_profile",
        "proxy_route": False,
        "note": "Additional public profile source slots such as Mastodon, GitLab, and Stack Overflow.",
    },
    "hunter": {
        "function": "connectors.email.hunter_email_intel_lookup",
        "credential_refs": ["HUNTER_API_KEY_REF"],
        "admin_section": "email_intel",
        "proxy_route": True,
        "note": "Domain search, email finder, and verifier for authorized business workflows.",
    },
    "hibp": {
        "function": "connectors.email.hibp_breach_exposure_lookup",
        "credential_refs": ["HIBP_API_KEY_REF"],
        "admin_section": "email_intel",
        "proxy_route": True,
        "note": "Breach exposure checks by email under HIBP API terms.",
    },
    "email-validation": {
        "function": "connectors.email.email_validation_lookup",
        "credential_refs": [],
        "admin_section": "email_intel",
        "proxy_route": False,
        "note": "Local syntax validation now; MX/deliverability provider can be added behind this slot.",
    },
    "people-data-labs": {
        "function": "connectors.person.people_data_labs_enrichment",
        "credential_refs": ["PEOPLE_DATA_LABS_API_KEY_REF"],
        "admin_section": "person_enrichment",
        "proxy_route": True,
        "note": "Licensed person and company enrichment with consent or legitimate-interest controls.",
    },
    "fullcontact-slot": {
        "function": "connectors.person.fullcontact_style_enrichment_slot",
        "credential_refs": ["FULLCONTACT_API_KEY_REF"],
        "admin_section": "person_enrichment",
        "proxy_route": True,
        "note": "Reserved licensed enrichment provider slot.",
    },
    "twilio-lookup": {
        "function": "connectors.phone.phone_intel_placeholder",
        "credential_refs": ["TWILIO_ACCOUNT_SID_REF", "TWILIO_AUTH_TOKEN_REF"],
        "admin_section": "phone_intel",
        "proxy_route": True,
        "note": "Phone validation and carrier intelligence for known numbers only.",
    },
    "ipinfo": {
        "function": "connectors.ipinfo.ipinfo_placeholder",
        "credential_refs": ["IPINFO_TOKEN_REF"],
        "admin_section": "domain_intel",
        "proxy_route": True,
        "note": "IP ASN, geography, org, and privacy flag lookup.",
    },
    "web-search-indexes": {
        "function": "connectors.search.web_search_index_lookup",
        "credential_refs": ["BRAVE_SEARCH_API_KEY_REF", "SERPAPI_API_KEY_REF", "BING_SEARCH_API_KEY_REF", "TAVILY_API_KEY_REF", "EXA_API_KEY_REF"],
        "admin_section": "web_search",
        "proxy_route": True,
        "note": "Search index provider slot; configure one or more supported APIs.",
    },
    "business-contact-data": {
        "function": "connectors.business.google_places_business_lookup",
        "credential_refs": ["GOOGLE_PLACES_API_KEY_REF", "YELP_API_KEY_REF"],
        "admin_section": "business_contact",
        "proxy_route": True,
        "note": "Business and local-place contact data for organizations, not private-person discovery.",
    },
    "opencorporates": {
        "function": "connectors.business.opencorporates_company_lookup",
        "credential_refs": [],
        "admin_section": "business_contact",
        "proxy_route": False,
        "note": "Public company registry lookup slot preserving source attribution.",
    },
    "rdap-whois": {
        "function": "connectors.domain.rdap_domain_lookup",
        "credential_refs": [],
        "admin_section": "domain_intel",
        "proxy_route": False,
        "note": "Public RDAP domain data without unnecessary personal registrant storage.",
    },
    "securitytrails": {
        "function": "connectors.domain.securitytrails_domain_lookup",
        "credential_refs": ["SECURITYTRAILS_API_KEY_REF"],
        "admin_section": "domain_intel",
        "proxy_route": True,
        "note": "Licensed domain, DNS, and infrastructure intelligence.",
    },
    "builtwith-wappalyzer": {
        "function": "connectors.domain.technology_profile_lookup",
        "credential_refs": ["BUILTWITH_API_KEY_REF", "WAPPALYZER_API_KEY_REF"],
        "admin_section": "domain_intel",
        "proxy_route": True,
        "note": "Domain technology profiling provider slot.",
    },
    "dnsdb-style": {
        "function": "connectors.domain.passive_dns_lookup",
        "credential_refs": ["DNSDB_API_KEY_REF"],
        "admin_section": "domain_intel",
        "proxy_route": True,
        "note": "Licensed passive DNS provider slot.",
    },
    "external-engine-slot": {
        "function": "engine.external_normalized_results_adapter",
        "credential_refs": ["EXTERNAL_ENGINE_API_KEY_REF"],
        "admin_section": "external",
        "proxy_route": False,
        "note": "Normalized-results adapter only; prohibited bypass/evasion features stay out of scope.",
    },
}



def resolve_connector_function(function_path: str) -> object:
    module_path, function_name = function_path.rsplit(".", 1)
    module = import_module(f"social_hunter.{module_path}")
    return getattr(module, function_name)


def validate_provider_functions() -> dict[str, str]:
    results: dict[str, str] = {}
    for provider in provider_catalog():
        try:
            resolve_connector_function(provider.connector_function)
            results[provider.id] = "ok"
        except (ImportError, AttributeError, ValueError) as exc:
            results[provider.id] = f"{type(exc).__name__}: {exc}"
    return results

def provider_catalog() -> list[ProviderConfig]:
    catalog: list[ProviderConfig] = []
    for source in SOURCE_CAPABILITIES:
        meta = _PROVIDER_META[source.id]
        catalog.append(
            ProviderConfig(
                id=source.id,
                name=source.name,
                category=source.category,
                source_id=source.id,
                target_types=source.target_types,
                status=source.status,
                connector_function=str(meta["function"]),
                credential_refs=list(meta["credential_refs"]),
                admin_section=str(meta["admin_section"]),
                proxy_route_supported=bool(meta["proxy_route"]),
                terms_note=source.terms_note,
                data_returned=source.data_returned,
                note=str(meta["note"]),
            )
        )
    return catalog


def default_api_key_references() -> list[ApiKeyReference]:
    refs: list[ApiKeyReference] = []
    for provider in provider_catalog():
        if not provider.credential_refs:
            refs.append(
                ApiKeyReference(
                    provider=provider.name,
                    provider_id=provider.id,
                    source_id=provider.source_id,
                    credential_type="none",
                    connector_function=provider.connector_function,
                    vault_reference="",
                    enabled=provider.status == "ready",
                    notes="No API credential required for this source slot.",
                )
            )
            continue
        for credential_ref in provider.credential_refs:
            refs.append(
                ApiKeyReference(
                    provider=provider.name,
                    provider_id=provider.id,
                    source_id=provider.source_id,
                    credential_type=credential_ref,
                    connector_function=provider.connector_function,
                    vault_reference="REPLACE_WITH_VAULT_REFERENCE",
                    enabled=False,
                    notes=provider.note,
                )
            )
    return refs


def default_proxy_route_rules() -> list[ProxyRouteRule]:
    return [
        ProxyRouteRule(
            id="provider-api-egress",
            label="Provider API egress",
            category="provider_api",
            enabled=False,
            proxy_required=False,
            provider_ids=[provider.id for provider in provider_catalog() if provider.proxy_route_supported],
            allowed_domains=[
                "api.hunter.io",
                "haveibeenpwned.com",
                "api.peopledatalabs.com",
                "lookups.twilio.com",
                "api.search.brave.com",
                "serpapi.com",
                "maps.googleapis.com",
                "api.yelp.com",
                "api.securitytrails.com",
                "ipinfo.io",
            ],
            note="Optional controlled proxy route for approved provider APIs only.",
        ),
        ProxyRouteRule(
            id="public-indexes",
            label="Search index providers",
            category="web_search",
            enabled=False,
            proxy_required=False,
            provider_ids=["web-search-indexes"],
            allowed_domains=["api.search.brave.com", "serpapi.com"],
            note="Search-index API routing; no stealth browser automation or CAPTCHA bypass.",
        ),
        ProxyRouteRule(
            id="public-profile-direct",
            label="Public profile API direct route",
            category="username_profile",
            enabled=True,
            proxy_required=False,
            provider_ids=["github-users", "reddit-api", "x-user-lookup"],
            allowed_domains=["api.github.com", "oauth.reddit.com", "api.x.com"],
            note="Use official profile APIs directly by default; credentials remain Vault-backed.",
        ),
    ]
