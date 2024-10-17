from rest_framework import serializers
from .models import Borrowing
from books.serializers import BookSerializer

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
