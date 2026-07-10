"""Billing routes for Social Hunter."""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from social_hunter.auth.middleware import AuthContext, require_auth
from social_hunter.models import PlanResponse
from social_hunter.services.billing import PLANS, billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans() -> list[PlanResponse]:
    """List available plans."""
    return [
        PlanResponse(
            id=plan_id,
            name=plan["name"],
            monthly_search_limit=plan["monthly_searches"],
            export_enabled=plan["exports"],
            api_access_enabled=plan["api_access"],
        )
        for plan_id, plan in PLANS.items()
    ]


@router.post("/checkout")
async def create_checkout(
    plan_id: str,
    context: Annotated[AuthContext, Depends(require_auth)],
) -> dict[str, str]:
    """Create checkout session."""
    # In production, get these from config
    success_url = "http://localhost:5173/billing/success"
    cancel_url = "http://localhost:5173/billing/cancel"

    return await billing_service.create_checkout_session(
        user_id=context.user_id,
        plan_id=plan_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Annotated[str, Header(alias="Stripe-Signature")],
) -> dict[str, bool]:
    """Handle Stripe webhook."""
    payload = await request.body()
    return await billing_service.handle_webhook(payload, stripe_signature)


@router.get("/portal")
async def customer_portal(
    context: Annotated[AuthContext, Depends(require_auth)],
) -> dict[str, str]:
    """Get customer portal URL."""
    # In production, lookup customer_id from user record
    customer_id = "cus_example"
    return_url = "http://localhost:5173/settings"

    url = await billing_service.get_customer_portal(customer_id, return_url)
    return {"url": url}
