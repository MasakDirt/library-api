from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from books.models import Book
from borrowings.validation import validate_borrowing


class Borrowing(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.email} borrowed {self.book.title}"

    def calculate_money_to_pay(self) -> Decimal:
        days = Decimal((self.expected_return_date - self.borrow_date).days)
        daily_fee = Decimal(self.book.daily_fee)

        return (days * daily_fee).quantize(Decimal("0.01"))

    def clean(self) -> None:
        validate_borrowing(
            self.borrow_date, self.expected_return_date, ValidationError
        )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        return super().save(*args, **kwargs)
