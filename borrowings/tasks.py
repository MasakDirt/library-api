import asyncio
import os
from datetime import date

import httpx
from celery import shared_task
from dotenv import load_dotenv

from borrowings.models import Borrowing


load_dotenv()


@shared_task
def check_overdue_borrowings() -> None:
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=date.today(),
        actual_return_date__isnull=True
    )

    message = ""
    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"User: {borrowing.user.email} has an overdue book!\n"
                f"Book Title: {borrowing.book.title}\n"
                f"Borrow Date: {borrowing.borrow_date}\n"
                f"Expected Return Date: {borrowing.expected_return_date}\n"
            )
    else:
        message = "There are no borrowings overdue today!"

    async def send_overdue():
        async with httpx.AsyncClient() as client:
            await client.post(
                f"http://{os.getenv('TELEGRAM_BOT_HOST')}:"
                f"{os.getenv('TELEGRAM_BOT_PORT')}/overdue/",
                json={"message": message}
            )

    asyncio.run(send_overdue())
