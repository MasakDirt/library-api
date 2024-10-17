import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
        book_data = validated_data.pop("book")
        book = get_object_or_404(Book, id=book_data.id)
        if book.inventory < 1:
            raise ValidationError("The following book is not available")
        with transaction.atomic():
            borrowing = Borrowing.objects.create(
                **validated_data, book=book
            )
            book.inventory -= 1
            book.save()
        return borrowing
