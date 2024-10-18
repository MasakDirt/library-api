import stripe
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer
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
                {"error": "Платёж уже завершён или не может быть оплачен"},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Borrowing Payment for {payment.borrowing.book.title}",
                        },
                        "unit_amount": int(payment.money_to_pay * 100),
                        # Stripe принимает сумму в центах
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url="https://yourdomain.com/success",
                cancel_url="https://yourdomain.com/cancel",
            )

            # Сохраняем данные сессии в объекте Payment
            payment.session_id = session.id
            payment.session_url = session.url
            payment.save()

            return Response({
                "sessionId": session.id,
                "sessionUrl": session.url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
