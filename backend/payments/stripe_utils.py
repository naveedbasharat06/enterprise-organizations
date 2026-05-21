import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_LABELS = {
    'basic':        'Basic',
    'professional': 'Professional',
    'premium':      'Premium',
}

# Storage included per plan in MB
STORAGE_BY_PLAN = {
    'basic':        5 * 1024,
    'professional': 20 * 1024,
    'premium':      50 * 1024,
}

# Max organizations a subscriber can own per plan
MAX_ORGS_BY_PLAN = {
    'basic':        1,
    'professional': 1,
    'premium':      5,
}

# Features unlocked per plan
PLAN_FEATURES = {
    'basic':        {'can_use_recording': False},
    'professional': {'can_use_recording': True},
    'premium':      {'can_use_recording': True},
}


def get_price_id(plan, billing_cycle):
    ids = settings.STRIPE_PRICE_IDS.get(plan, {})
    return ids.get(billing_cycle, '')


def get_metered_price_id(plan):
    return settings.STRIPE_PRICE_IDS.get(plan, {}).get('metered', '')


def create_checkout_session(pending_token, plan, billing_cycle, customer_email, frontend_url):
    price_id = get_price_id(plan, billing_cycle)

    # Only include the flat subscription price here.
    # The metered overage price is attached to the subscription after checkout
    # completes — Stripe rejects sessions mixing monthly and annual intervals.
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        customer_email=customer_email,
        line_items=[{'price': price_id, 'quantity': 1}],
        metadata={'pending_token': str(pending_token), 'plan': plan, 'billing_cycle': billing_cycle},
        success_url=f"{frontend_url}/onboarding/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_url}/onboarding?cancelled=1",
        subscription_data={'metadata': {'pending_token': str(pending_token)}},
    )
    return session


def get_meter_event_name(plan):
    """Return the Stripe meter event name for a given plan key."""
    return f"rolebase_{plan}_storage"


def report_storage_usage(customer_id, plan, quantity_mb):
    """
    Report storage overage to Stripe using the new Meters API (2025-03-31.basil+).
    quantity_mb is converted to GB (rounded up) before reporting.
    """
    if not customer_id or not plan:
        return
    import math
    quantity_gb = math.ceil(quantity_mb / 1024)
    if quantity_gb < 1:
        return
    stripe.billing.MeterEvent.create(
        event_name=get_meter_event_name(plan),
        payload={
            'value':              str(quantity_gb),
            'stripe_customer_id': customer_id,
        },
    )


def get_billing_dates(billing_cycle):
    now = timezone.now()
    if billing_cycle == 'annual':
        return now, now + timedelta(days=365)
    return now, now + timedelta(days=30)
