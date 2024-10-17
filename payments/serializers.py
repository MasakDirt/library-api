from borrowings.serializers import BorrowingSerializer
from rest_framework import serializers

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
    borrowing = BorrowingSerializer(many=False, read_only=True)
