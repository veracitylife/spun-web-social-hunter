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


def paypal_checkout_url(plan_id: str) -> str:
    plan = PLANS[plan_id]
    params = {
        "cmd": "_xclick",
        "business": PAYPAL_EMAIL,
        "currency_code": "USD",
        "item_name": f"Social Hunter {plan['name']} Plan",
        "amount": str(plan["amount"]),
    }
    return "https://www.paypal.com/cgi-bin/webscr?" + urlencode(params)
