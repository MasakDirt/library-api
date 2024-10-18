from rest_framework import serializers

from borrowings.serializers import BorrowingReadSerializer
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay"
        )


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing = serializers.CharField(
        source="borrowing.book.title",
        read_only=True
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "money_to_pay"
        )


class PaymentRetrieveSerializer(PaymentSerializer):
    borrowing = BorrowingReadSerializer(many=False, read_only=True)
