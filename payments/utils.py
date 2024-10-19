import stripe
from django.conf import settings

from borrowings.models import Borrowing
from payments.models import Payment


FINE_MULTIPLIER = 2


def create_stripe_session(borrowing: Borrowing, borrowing_type: str = "Payment"):
    if borrowing_type == "Fine":
        borrowing_price = int(borrowing.calculate_money_to_fine() * 100) * FINE_MULTIPLIER
    else:
        borrowing_price = int(borrowing.calculate_money_to_pay() * 100)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    return borrowing_price, stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing {borrowing_type} for "
                        f"{borrowing.book.title}",
                    },
                    "unit_amount": borrowing_price,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="https://google.com",
        cancel_url="https://...",
    )


def create_payment(borrowing: Borrowing):
    borrowing_price, session = create_stripe_session(borrowing)

    Payment.objects.create(
        type="PAYMENT",
        borrowing=borrowing,
        session_id=session.id,
        session_url=session.url,
        money_to_pay=borrowing_price,
    )


def create_fine(borrowing: Borrowing):
    borrowing_price, session = create_stripe_session(
        borrowing, borrowing_type="Fine"
    )

    Payment.objects.create(
        type="FINE",
        borrowing=borrowing,
        session_id=session.id,
        session_url=session.url,
        money_to_pay=borrowing_price,
    )
