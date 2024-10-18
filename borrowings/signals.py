import asyncio
from typing import Type

import stripe
from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from payments.models import Payment
from telegram_bot.notify import notify_borrowing_create


@receiver(post_save, sender=Borrowing)
def borrowing_created(
        sender: Type[Model],
        instance: Borrowing,
        created: bool,
        **kwargs
) -> None:
    if created:
        asyncio.run(notify_borrowing_create(instance))

        borrowing_price = int(instance.calculate_money_to_pay() * 100)

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing Payment for {instance.book.title}",
                    },
                    "unit_amount": borrowing_price,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://google.com",
            cancel_url="https://...",
        )

        Payment.objects.create(
            borrowing=instance,
            session_id=session.id,
            session_url=session.url,
            money_to_pay=borrowing_price,
        )
