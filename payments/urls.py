from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payments.views import PaymentViewSet, stripe_webhook

app_name = "payments"

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
    path("webhook/stripe/", stripe_webhook, name="stripe-webhook"),
]
