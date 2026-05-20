import stripe
import json
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from accounts.models import Organization, User, StorageUsage, PendingOnboarding
from .stripe_utils import (
    create_checkout_session, get_billing_dates,
    PLAN_FEATURES, STORAGE_BY_PLAN,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        org_name      = data.get('org_name', '').strip()
        org_type      = data.get('org_type', 'other')
        org_size      = data.get('org_size', '')
        plan          = data.get('plan', 'basic')
        billing_cycle = data.get('billing_cycle', 'monthly')
        username      = data.get('username', '').strip()
        email         = data.get('email', '').strip()
        password      = data.get('password', '')

        # Validate required fields
        if not all([org_name, username, email, password]):
            return Response({'error': 'org_name, username, email and password are required.'}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'An account with this email already exists.'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'This username is already taken.'}, status=400)

        if Organization.objects.filter(name=org_name).exists():
            return Response({'error': 'An organization with this name already exists.'}, status=400)

        if plan not in ('basic', 'professional', 'premium'):
            return Response({'error': 'Invalid plan.'}, status=400)

        if billing_cycle not in ('monthly', 'annual'):
            return Response({'error': 'Invalid billing_cycle.'}, status=400)

        # Store pending onboarding record (password hashed, not sent to Stripe)
        pending = PendingOnboarding.objects.create(
            org_name=org_name,
            org_type=org_type,
            org_size=org_size,
            plan=plan,
            billing_cycle=billing_cycle,
            username=username,
            email=email,
            password_hash=make_password(password),
        )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        try:
            session = create_checkout_session(
                pending_token=pending.token,
                plan=plan,
                billing_cycle=billing_cycle,
                customer_email=email,
                frontend_url=frontend_url,
            )
            pending.stripe_session_id = session.id
            pending.save(update_fields=['stripe_session_id'])
            return Response({'checkout_url': session.url})
        except Exception as e:
            pending.delete()
            return Response({'error': str(e)}, status=500)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload    = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            if webhook_secret and webhook_secret != 'whsec_your-webhook-secret-here':
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            else:
                event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            return Response({'error': str(e)}, status=400)

        if event['type'] == 'checkout.session.completed':
            self._handle_checkout_completed(event['data']['object'])

        elif event['type'] == 'invoice.paid':
            self._handle_invoice_paid(event['data']['object'])

        elif event['type'] == 'invoice.payment_failed':
            self._handle_payment_failed(event['data']['object'])

        elif event['type'] == 'customer.subscription.deleted':
            self._handle_subscription_cancelled(event['data']['object'])

        return Response({'status': 'ok'})

    def _handle_checkout_completed(self, session):
        pending_token = session.get('metadata', {}).get('pending_token')
        if not pending_token:
            return

        try:
            pending = PendingOnboarding.objects.get(token=pending_token, is_completed=False)
        except PendingOnboarding.DoesNotExist:
            return

        if pending.is_expired():
            return

        features = PLAN_FEATURES.get(pending.plan, {})
        storage_mb = STORAGE_BY_PLAN.get(pending.plan, 5120)
        period_start, period_end = get_billing_dates(pending.billing_cycle)

        # Get metered subscription item ID for storage overage reporting
        metered_item_id = ''
        subscription_id = session.get('subscription', '')
        if subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id, expand=['items'])
                for item in sub['items']['data']:
                    if item['price'].get('recurring', {}).get('usage_type') == 'metered':
                        metered_item_id = item['id']
                        break
            except Exception:
                pass

        org = Organization.objects.create(
            name=pending.org_name,
            org_type=pending.org_type,
            org_size=pending.org_size,
            plan=pending.plan,
            billing_cycle=pending.billing_cycle,
            stripe_customer_id=session.get('customer', ''),
            stripe_subscription_id=subscription_id,
            stripe_metered_item_id=metered_item_id,
            storage_included_mb=storage_mb,
            storage_used_mb=0,
            billing_period_start=period_start,
            billing_period_end=period_end,
            can_use_recording=features.get('can_use_recording', False),
            is_active=True,
        )

        user = User(
            username=pending.username,
            email=pending.email,
            role=User.ROLE_SUPER_ADMIN,
            organization=org,
        )
        user.password = pending.password_hash
        user.save()

        pending.is_completed = True
        pending.save(update_fields=['is_completed'])

    def _handle_invoice_paid(self, invoice):
        customer_id = invoice.get('customer')
        if not customer_id:
            return
        try:
            org = Organization.objects.get(stripe_customer_id=customer_id)
        except Organization.DoesNotExist:
            return

        period_start, period_end = get_billing_dates(org.billing_cycle)
        org.billing_period_start = period_start
        org.billing_period_end   = period_end
        org.storage_used_mb      = 0
        org.save(update_fields=['billing_period_start', 'billing_period_end', 'storage_used_mb'])

        StorageUsage.objects.filter(organization=org, reported_to_stripe=True).delete()

    def _handle_payment_failed(self, invoice):
        customer_id = invoice.get('customer')
        if not customer_id:
            return
        try:
            org = Organization.objects.get(stripe_customer_id=customer_id)
            org.is_active = False
            org.save(update_fields=['is_active'])
        except Organization.DoesNotExist:
            pass

    def _handle_subscription_cancelled(self, subscription):
        sub_id = subscription.get('id')
        if not sub_id:
            return
        try:
            org = Organization.objects.get(stripe_subscription_id=sub_id)
            org.is_active = False
            org.save(update_fields=['is_active'])
        except Organization.DoesNotExist:
            pass


class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if not org:
            return Response({'error': 'No organization assigned.'}, status=404)

        return Response({
            'plan':               org.plan,
            'billing_cycle':      org.billing_cycle,
            'is_active':          org.is_active,
            'can_use_recording':  org.can_use_recording,
            'billing_period_end': org.billing_period_end,
            'storage_included_gb': org.storage_included_gb(),
            'storage_used_gb':    org.storage_used_gb(),
            'storage_overage_gb': org.storage_overage_gb(),
        })


class StorageUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if not org:
            return Response({'error': 'No organization assigned.'}, status=404)

        records = StorageUsage.objects.filter(organization=org).order_by('-recorded_at')[:20]
        data = [
            {
                'file_type':    r.file_type,
                'file_size_mb': round(r.file_size_mb, 2),
                'recorded_at':  r.recorded_at,
            }
            for r in records
        ]

        overage_rate = {'basic': 5.0, 'professional': 4.0, 'premium': 3.0}.get(org.plan, 5.0)
        estimated_charge = round(org.storage_overage_gb() * overage_rate, 2)

        return Response({
            'storage_included_mb':  org.storage_included_mb,
            'storage_used_mb':      round(org.storage_used_mb, 2),
            'storage_included_gb':  org.storage_included_gb(),
            'storage_used_gb':      org.storage_used_gb(),
            'storage_overage_gb':   org.storage_overage_gb(),
            'overage_rate_per_gb':  overage_rate,
            'estimated_overage_charge': estimated_charge,
            'recent_uploads':       data,
        })
