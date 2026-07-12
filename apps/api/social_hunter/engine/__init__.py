from social_hunter.engine.public_profile_checker import PublicProfileChecker, ProfileCheckResult, ProfileSource


async def external_normalized_results_adapter(target: str) -> list[dict]:
    return [
        {
            "source": "External normalized-results adapter",
            "status": "skipped",
            "target": target,
            "message": (
                "External engine slot is wired for normalized lawful results only. "
                "Bypass, evasion, and CAPTCHA-solving mechanics are not implemented here."
            ),
        }
    ]


__all__ = [
    "PublicProfileChecker",
    "ProfileCheckResult",
    "ProfileSource",
    "external_normalized_results_adapter",
]
