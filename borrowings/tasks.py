# from datetime import date
# from celery import shared_task
# from django.core.mail import send_mail
# from .models import Borrowing
# import requests


from celery import Celery

import os
import django
from celery import shared_task

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_api.settings")
django.setup()
from books.models import Book

app = Celery("tasks", broker="redis://localhost:6379/0")


@shared_task
def test_celery():
    # return Book.objects.count()
    print("Celery is working! But i still have problem in shell")
    return "Celery is working!(test time task)"

# if __name__ == "__main__":
#     result = test_celery.delay()
#     print(result.get())


# TELEGRAM_BOT_TOKEN = 'your-telegram-bot-token'
# TELEGRAM_CHAT_ID = 'your-telegram-chat-id'

# @shared_task
# def check_overdue_borrowings() -> None:
#     """
#     Task to check for overdue borrowings and send notifications to Telegram chat.
#     """
#     overdue_borrowings = Borrowing.objects.filter(expected_return_date__lte=date.today(), actual_return_date__isnull=True)
#
#     if overdue_borrowings.exists():
#         for borrowing in overdue_borrowings:
#             message = (
#                 f"User: {borrowing.user.email} has an overdue book!\n"
#                 f"Book Title: {borrowing.book.title}\n"
#                 f"Expected Return Date: {borrowing.expected_return_date}\n"
#                 f"Borrow Date: {borrowing.borrow_date}\n"
#             )
#             send_telegram_message(message)
#     else:
#         send_telegram_message("No borrowings overdue today!")
#
# def send_telegram_message(message: str) -> None:
#     """
#     Helper function to send a message to the specified Telegram chat.
#     """
#     url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
#     data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
#     response = requests.post(url, data=data)
#     if response.status_code != 200:
#         raise Exception(f"Error sending message: {response.text}")
