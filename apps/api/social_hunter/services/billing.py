from urllib.parse import urlencode

PAYPAL_EMAIL = "techpronow@gmail.com"

PLANS = {
    "starter": {
        "name": "Starter",
        "amount": 49,
        "monthly_searches": 250,
        "exports": True,
        "api_access": False,
    },
    "growth": {
        "name": "Growth",
        "amount": 149,
        "monthly_searches": 1500,
        "exports": True,
        "api_access": False,
    },
    "operator": {
        "name": "Operator",
        "amount": 399,
        "monthly_searches": 7500,
        "exports": True,
        "api_access": True,
    },
}


def paypal_checkout_url(plan_id: str, *, receiver_email: str | None = None, amount: float | int | None = None, currency: str = "USD", item_name: str | None = None) -> str:
    plan = PLANS.get(plan_id, {})
    label = item_name or f"Social Hunter {plan.get('name', plan_id.title())} Plan"
    price = amount if amount is not None else plan.get("amount", 0)
    params = {
        "cmd": "_xclick",
        "business": receiver_email or PAYPAL_EMAIL,
        "currency_code": currency,
        "item_name": label,
        "amount": str(price),
    }
    return "https://www.paypal.com/cgi-bin/webscr?" + urlencode(params)
