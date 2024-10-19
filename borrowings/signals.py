import asyncio
from typing import Type

from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from borrowings.models import Borrowing
from payments.utils import create_payment
from telegram_bot.notify import notify_borrowing_create


@receiver(post_save, sender=Borrowing)
def borrowing_created(
    sender: Type[Model], instance: Borrowing, created: bool, **kwargs
) -> None:
    if created:
        asyncio.run(notify_borrowing_create(instance))

        create_payment(instance)
