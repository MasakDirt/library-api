import os
import random

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Bot


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

bot = Bot(token=TOKEN)

app = FastAPI()


class BorrowingData(BaseModel):
    user_email: str
    book_title: str
    borrow_date: str
    expected_return_date: str


async def send_telegram_message(message: str):
    await bot.send_message(CHAT_ID, message)


@app.post("/notify/")
async def notify_borrowing(data: BorrowingData):
    message = random.choice(MESSAGES).format(
        data.user_email,
        data.book_title,
        data.borrow_date,
        data.expected_return_date
    )
    await send_telegram_message(message)
    return {"status": "success", "message": message}


@app.post("/overdue/")
async def notify_overdue_borrowing(message: str):
    await send_telegram_message(message)
    return {"status": "success", "message": message}
