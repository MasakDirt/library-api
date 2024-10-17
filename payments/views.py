from rest_framework import viewsets

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentRetrieveSerializer
)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer

        if self.action == "retrieve":
            return PaymentRetrieveSerializer

        return self.serializer_class
