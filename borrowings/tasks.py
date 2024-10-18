import asyncio
from datetime import date
from celery import shared_task
from borrowings.models import Borrowing
from telegram_bot.notify import notify_overdue_borrowings


@shared_task
def check_overdue_borrowings() -> None:
    """
    Task to check for overdue borrowings and send notifications to Telegram chat.
    """
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=date.today(),
        actual_return_date__isnull=True
    )
    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"User: {borrowing.user.email} has an overdue book!\n"
                f"Book Title: {borrowing.book.title}\n"
                f"Borrow Date: {borrowing.borrow_date}\n"
                f"Expected Return Date: {borrowing.expected_return_date}\n"
            )
            asyncio.run(notify_overdue_borrowings(message))
    else:
        asyncio.run(notify_overdue_borrowings(
            "There are no borrowings overdue today!")
        )
