"""Stripe billing integration for Social Hunter."""
import os
from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import HTTPException, status

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Plan configuration
PLANS = {
    "free": {
        "name": "Free",
        "price_id": None,
        "monthly_searches": 10,
        "exports": False,
        "api_access": False,
    },
    "hobby": {
        "name": "Hobby",
        "price_id": os.getenv("STRIPE_HOBBY_PRICE_ID", ""),
        "monthly_searches": 100,
        "exports": True,
        "api_access": False,
    },
    "pro": {
        "name": "Pro",
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID", ""),
        "monthly_searches": 1000,
        "exports": True,
        "api_access": True,
    },
    "team": {
        "name": "Team",
        "price_id": os.getenv("STRIPE_TEAM_PRICE_ID", ""),
        "monthly_searches": 10000,
        "exports": True,
        "api_access": True,
    },
}


class BillingService:
    """Stripe billing service."""

    def __init__(self):
        self.plans = PLANS

    async def create_checkout_session(
        self,
        user_id: str,
        plan_id: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, str]:
        """Create Stripe checkout session."""
        if plan_id not in self.plans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan",
            )

        plan = self.plans[plan_id]
        if not plan["price_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot checkout free plan",
            )

        try:
            session = stripe.checkout.Session.create(
                customer_email=None,  # Will be collected on checkout
                metadata={"user_id": user_id, "plan_id": plan_id},
                line_items=[{
                    "price": plan["price_id"],
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    "metadata": {"user_id": user_id},
                },
            )
            return {"session_id": session.id, "url": session.url}
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe error: {exc}",
            )

    async def handle_webhook(self, payload: bytes, signature: str) -> dict[str, Any]:
        """Handle Stripe webhook."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, stripe_webhook_secret
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload",
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            )

        # Handle events
        if event["type"] == "checkout.session.completed":
            await self._handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            await self._handle_subscription_cancelled(event["data"]["object"])

        return {"received": True, "type": event["type"]}

    async def _handle_checkout_completed(self, session: dict) -> None:
        """Handle successful checkout."""
        user_id = session["metadata"]["user_id"]
        plan_id = session["metadata"]["plan_id"]
        subscription_id = session["subscription"]

        # Update user in your database
        # await update_user_subscription(user_id, plan_id, subscription_id)
        print(f"User {user_id} subscribed to {plan_id}")

    async def _handle_payment_succeeded(self, invoice: dict) -> None:
        """Handle successful payment."""
        subscription_id = invoice["subscription"]
        # Update subscription status
        print(f"Payment succeeded for subscription {subscription_id}")

    async def _handle_subscription_cancelled(self, subscription: dict) -> None:
        """Handle subscription cancellation."""
        user_id = subscription["metadata"]["user_id"]
        # Downgrade to free plan
        # await update_user_plan(user_id, "free")
        print(f"User {user_id} cancelled subscription")

    async def get_customer_portal(self, customer_id: str, return_url: str) -> str:
        """Get customer portal URL."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe error: {exc}",
            )

    async def cancel_subscription(self, subscription_id: str) -> None:
        """Cancel subscription at period end."""
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
        except stripe.error.StripeError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe error: {exc}",
            )


billing_service = BillingService()
