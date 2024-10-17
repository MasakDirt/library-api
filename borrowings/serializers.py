import datetime

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed

from books.models import Book
from .models import Borrowing
from books.serializers import BookSerializer
from .validation import validate_borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date"
        ]

class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ["id", "book", "expected_return_date", "actual_return_date"]

    def validate(self, attrs) -> dict:
        expected_return_date = attrs.get("expected_return_date")

        if expected_return_date is not None:
            validate_borrowing(
                borrow_date=datetime.date.today(),
                expected_return_date=expected_return_date,
                error_to_raise=serializers.ValidationError
            )

        return attrs

    def create(self, validated_data) -> Borrowing:
        with transaction.atomic():
            book_data = validated_data.pop("book")
            book = Book.objects.get(id=book_data.id)
            if book.inventory < 1:
                raise ValidationError("the following book is not available")
            borrowing = Borrowing.objects.create(
                **validated_data, book=book_data
            )
            book.inventory -= 1
            book.save()
            return borrowing
