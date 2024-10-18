import os
import random

from dotenv import load_dotenv
from telegram import Bot

from borrowings.models import Borrowing


load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MESSAGES = [
    """
    CONGRATULATIONS!🎉🥳💗
{} borrow book '{}' from {} to {}.
Don't forget to return it!😁
    """,

    """
    Great news!📚✨
{} has borrowed '{}' from {} to {}. 📅
Enjoy the reading journey! 📖
""",

    """
    Hello, {}! 🌟
You've taken '{}' from {} until {}.
Make the most of it! 🚀
    """,

    """
    Reminder! 🔔
{} checked out '{}' starting on {} and must return by {}.
Happy reading! 😊
    """,

    """
    Hi there, {}! 👋
You've borrowed '{}' from {} to {}.
Please remember the return date! 📅
    """,

    """
    Heads up, {}! ⚡️
You've got '{}' from {} until {}.
Don’t forget to enjoy the book! 📘
    """,

    """
    Friendly reminder! 🌸
{} just grabbed '{}' from {} to {}.
Make sure to bring it back on time! ⏰
    """,

    """
    Book alert! 📚💫
{} has checked out '{}' from {} and it's due by {}.
Keep reading and enjoy! 🌟
    """,

    """
    Congrats! 🎉
{} has loaned '{}' between {} and {}.
Happy reading and don't miss the return date! 🔖
    """
]


def get_bot() -> Bot:
    return Bot(token=TOKEN)


async def notify_borrowing_create(instance: Borrowing):
    bot = get_bot()
    strdate = "%d %B %y"

    async with bot:
        await bot.send_message(
            CHAT_ID,
            random.choice(MESSAGES).format(
                instance.user.email,
                instance.book.title,
                instance.borrow_date.strftime(strdate),
                instance.expected_return_date.strftime(strdate),
            )
        )
