"""
Creates all Stripe products, prices, and meters for RoleBase subscription plans.
Run once after setting STRIPE_SECRET_KEY in your .env:

    docker compose exec backend python manage.py setup_stripe

Copy the printed Price IDs into your .env file, then rebuild Docker.
"""
import stripe
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create Stripe products, prices, and meters for all subscription plans'

    PLANS = [
        {
            'key':           'basic',
            'name':          'Basic',
            'monthly_cents': 2000,    # $20/month
            'annual_cents':  19200,   # $192/year
            'metered_cents': 500,     # $5 per GB overage
            'env_prefix':    'STRIPE_BASIC',
        },
        {
            'key':           'professional',
            'name':          'Professional',
            'monthly_cents': 4000,    # $40/month
            'annual_cents':  38400,   # $384/year
            'metered_cents': 400,     # $4 per GB overage
            'env_prefix':    'STRIPE_PRO',
        },
        {
            'key':           'premium',
            'name':          'Premium',
            'monthly_cents': 8000,    # $80/month
            'annual_cents':  76800,   # $768/year
            'metered_cents': 300,     # $3 per GB overage
            'env_prefix':    'STRIPE_PREMIUM',
        },
    ]

    def _get_or_create_meter(self, event_name, plan_name):
        """Return existing active meter for event_name, or create a new one."""
        meters = stripe.billing.Meter.list(limit=100)
        for m in meters.data:
            if m.event_name == event_name and m.status == 'active':
                self.stdout.write(f"  ↩ Reusing existing meter: {event_name}")
                return m
        return stripe.billing.Meter.create(
            display_name=f"RoleBase {plan_name} Storage (GB)",
            event_name=event_name,
            default_aggregation={"formula": "sum"},
            customer_mapping={
                "event_payload_key": "stripe_customer_id",
                "type": "by_id",
            },
            value_settings={"event_payload_key": "value"},
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if not stripe.api_key:
            self.stderr.write('ERROR: STRIPE_SECRET_KEY is not set in your .env file.')
            return

        self.stdout.write('\n=== Creating Stripe Products, Prices & Meters ===\n')

        for plan in self.PLANS:
            self.stdout.write(f"\n→ Setting up {plan['name']} plan...")

            # ── Flat subscription product ──────────────────────────────────
            product = stripe.Product.create(
                name=f"RoleBase {plan['name']}",
                description=f"RoleBase {plan['name']} — RBAC dashboard subscription",
            )

            monthly = stripe.Price.create(
                product=product.id,
                unit_amount=plan['monthly_cents'],
                currency='usd',
                recurring={'interval': 'month'},
                nickname=f"{plan['name']} Monthly",
            )

            annual = stripe.Price.create(
                product=product.id,
                unit_amount=plan['annual_cents'],
                currency='usd',
                recurring={'interval': 'year'},
                nickname=f"{plan['name']} Annual",
            )

            # ── Metered storage overage (new Stripe Meters API) ───────────
            # Step 1: get existing meter or create a new one
            event_name = f"rolebase_{plan['key']}_storage"
            meter = self._get_or_create_meter(event_name, plan['name'])

            # Step 2: create a product and price that references the meter
            metered_product = stripe.Product.create(
                name=f"RoleBase {plan['name']} Storage Overage",
                description=f"Per-GB storage overage for {plan['name']} plan",
            )

            metered = stripe.Price.create(
                product=metered_product.id,
                unit_amount=plan['metered_cents'],
                currency='usd',
                recurring={
                    'interval':   'month',
                    'usage_type': 'metered',
                    'meter':      meter.id,
                },
                nickname=f"{plan['name']} Storage Overage per GB",
            )

            self.stdout.write(f"  ✓ {plan['name']} created (meter event: {event_name})")
            self.stdout.write(f"\n# {plan['name']} Plan — paste into backend/.env")
            self.stdout.write(f"{plan['env_prefix']}_MONTHLY_PRICE_ID={monthly.id}")
            self.stdout.write(f"{plan['env_prefix']}_ANNUAL_PRICE_ID={annual.id}")
            self.stdout.write(f"{plan['env_prefix']}_METERED_PRICE_ID={metered.id}")

        self.stdout.write('\n\n✓ All Stripe products, prices and meters created!')
        self.stdout.write('Copy the Price IDs above into backend/.env, then run:')
        self.stdout.write('  docker compose up --build\n')
