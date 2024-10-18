import stripe
from django.conf import settings
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

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

    @action(detail=True, methods=["post"])
    def create_payment(self, request, pk=None):
        payment = self.get_object()

        if payment.status != Payment.StatusChoices.PENDING:
            return Response(
                {"error": "Payment cannot be completed or already payed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Borrowing Payment for "
                                        f"{payment.borrowing.book.title}",
                            },
                            "unit_amount": int(payment.money_to_pay * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url="https://yourdomain.com/success",
                cancel_url="https://yourdomain.com/cancel",
            )

            payment.session_id = session.id
            payment.session_url = session.url
            payment.save()

            return Response(
                {"sessionId": session.id, "sessionUrl": session.url},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
