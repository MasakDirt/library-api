from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookListSerializer, BookSerializer

BOOK_URL = reverse("books:book-list")


def sample_book(**additional) -> Book:
    defaults = {
        "title": "Book title",
        "author": "Author Sample",
        "cover": "SOFT",
        "inventory": 10,
        "daily_fee": Decimal("1.04")
    }
    defaults.update(additional)

    return Book.objects.create(**defaults)


def get_detail(book_id: int) -> str:
    return reverse("books:book-detail", args=[book_id])


class BookAPITests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create(
            email="user",
            password="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_books(self) -> None:
        sample_book()
        sample_book(title="Test2", cover="HARD")
        sample_book(title="Test3", inventory=11)

        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_book_detail(self) -> None:
        book = sample_book()

        response = self.client.get(get_detail(book.id))
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
