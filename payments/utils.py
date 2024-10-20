import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse

from borrowings.models import Borrowing
from payments.models import Payment


FINE_MULTIPLIER = 2


def get_borrowing_price(
    borrowing: Borrowing,
    borrowing_type: str = "Payment"
) -> int:
    if borrowing_type == "Fine":
        borrowing_price = (
            int(
                borrowing.calculate_money_to_fine() * 100
            ) * FINE_MULTIPLIER
        )
    else:
        borrowing_price = int(borrowing.calculate_money_to_pay() * 100)

    return borrowing_price


def get_url(viewname: str, payment_id: int) -> str:
    return settings.SITE_URL + reverse(viewname, args=[payment_id])


def create_stripe_session(**kwargs) -> stripe.checkout.Session:
    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing {kwargs["borrowing_type"]} "
                                f"for {kwargs["borrowing"].book.title}",
                    },
                    "unit_amount": kwargs["borrowing_price"],
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=get_url("payments:payment-success", kwargs["payment"].id),
        cancel_url=get_url("payments:payment-cancel", kwargs["payment"].id),
    )


def create_payment_with_session(
    borrowing: Borrowing,
    borrowing_type: str = "Payment"
) -> None:
    borrowing_price = get_borrowing_price(borrowing, borrowing_type)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    with transaction.atomic():
        payment = Payment.objects.create(
            type=borrowing_type,
            borrowing=borrowing,
            money_to_pay=borrowing_price,
        )

        session = create_stripe_session(
            borrowing_type=borrowing_type,
            borrowing=borrowing,
            borrowing_price=borrowing_price,
            payment=payment,
        )

        payment.session_id = session.id
        payment.session_url = session.url
        payment.save()
