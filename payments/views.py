import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer,
)


stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "borrowing__user",
                "borrowing__book"
            )

        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        if self.action == "retrieve":
            return PaymentRetrieveSerializer

        return self.serializer_class

    @action(
        methods=["GET"],
        detail=True,
        url_path="success",
        url_name="success",
    )
    def payment_success(self, request: Request, pk: int = None) -> Response:
        """Endpoint for success url after payment"""

        session_id = get_object_or_404(Payment, pk=pk).session_id

        if not session_id:
            return Response(
                {"detail": "Session ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer = session.customer_details

            return Response(
                {
                    "detail": f"Thanks for your order, {customer.name}!",
                    "customer": {
                        "name": customer.name,
                        "email": customer.email,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["GET"],
        detail=True,
        url_path="cancel",
        url_name="cancel",
    )
    def payment_cancel(self, request: Request, pk: int = None) -> Response:
        """Endpoint for cancel url after payment"""

        payment = get_object_or_404(Payment, pk=pk)
        user = request.user

        if payment.borrowing.user != user and not user.is_staff:
            return Response(
                {"detail": "It`s not your payment! Be more attentive!"},
                status=status.HTTP_403_FORBIDDEN
            )

        if payment.status == "PENDING":
            if not payment.session_id:
                return Response(
                    {"detail": "Session ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "detail": f"Okay, '{user.email}' you can pay a little "
                              f"bit later, but during 24 hours!",
                    "payment": {
                        "payment_id": payment.id,
                        "session_id": payment.session_id,
                        "session_url": payment.session_url,
                    },
                    "user_email": user.email,
                },
                status=status.HTTP_200_OK,
            )
        elif payment.status == "PAID":
            return Response(
                {
                    "detail": f"Dear '{user.email}', you have already "
                              f"paid this borrowing!"
                },
                status=status.HTTP_200_OK
            )


def handle_successful_payment(session):
    payment = Payment.objects.get(session_id=session["id"])
    payment.status = "PAID"
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
        handle_successful_payment(session)

    return JsonResponse({"status": "success"}, status=200)
