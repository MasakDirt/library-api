from borrowings.models import Borrowing
from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT", _("Payment")
        FINE = "FINE", _("Fine")

    status = models.CharField(
        max_length=7,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    type = models.CharField(max_length=7, choices=TypeChoices.choices)
    borrowing = models.ForeignKey(
        Borrowing,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    session_url = models.URLField(max_length=255)
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.borrowing} - {self.status}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["borrowing", "session_id"],
                name="unique_borrowing_session_id"
            )
        ]
