from rest_framework import serializers

from books.serializers import BookRetrieveSerializer
from borrowings.models import Borrowing


class BorrowingListRetrieveSerializer(serializers.ModelSerializer):
    book = BookRetrieveSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date"
        )
