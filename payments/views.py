import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer,
)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("borrowing__book")
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        if self.action == "retrieve":
            return PaymentRetrieveSerializer

        return self.serializer_class


def handle_successful_payment(session):
    payment = Payment.objects.get(session_id=session["id"])
    payment.status = "Paid"
    payment.save()


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    endpoint_secret = settings.ENDPOINT_SECRET_WEBHOOK

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("session in webhook: ", session)
        handle_successful_payment(session)

    return JsonResponse({"status": "success"}, status=200)
