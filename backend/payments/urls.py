from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    StripeWebhookView,
    SubscriptionStatusView,
    StorageUsageView,
)

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/',                 StripeWebhookView.as_view(),          name='stripe-webhook'),
    path('subscription-status/',     SubscriptionStatusView.as_view(),     name='subscription-status'),
    path('storage-usage/',           StorageUsageView.as_view(),           name='storage-usage'),
]
