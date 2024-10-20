import asyncio
from typing import Type

import httpx
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from payments.utils import create_payment_with_session


@receiver(post_save, sender=Borrowing)
def borrowing_created(
    sender: Type[Model],
    instance: Borrowing,
    created: bool,
    **kwargs
) -> None:
    if created:
        create_payment_with_session(instance)

        borrowing_data = {
            "user_email": instance.user.email,
            "book_title": instance.book.title,
            "borrow_date": str(instance.borrow_date),
            "expected_return_date": str(instance.expected_return_date)
        }

        async def send_notification():
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8001/notify/",
                    json=borrowing_data
                )

        asyncio.run(send_notification())
