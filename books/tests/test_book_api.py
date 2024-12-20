from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import (
    BookListSerializer,
    BookRetrieveSerializer,
)


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


class UnAuthenticatedBookAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books(self) -> None:
        sample_book()
        sample_book(title="Test2", cover="HARD")
        sample_book(title="Test3", inventory=11)

        response = self.client.get(BOOK_URL)

        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_books(self):
        author = "Search"
        title = "tes"
        extra_book_title = sample_book(author=author)
        sample_book(title="Test2", author=author, cover="HARD")
        sample_book(title="Test3", inventory=11, author=author)
        extra_book_author = sample_book(title="Test3", inventory=11)

        for filter_field, filter_value, extra_book in [
            ("title", title, extra_book_title),
            ("author", author[:4], extra_book_author),
        ]:
            response = self.client.get(BOOK_URL, {filter_field: filter_value})
            books = Book.objects.filter(
                **{f"{filter_field}__icontains": filter_value}
            )
            self.assertNotIn(extra_book, books)
            serializer = BookListSerializer(books, many=True)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["results"], serializer.data)

    def test_book_detail(self) -> None:
        book = sample_book()

        response = self.client.get(get_detail(book.id))
        serializer = BookRetrieveSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class AuthenticatedBookAPITests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create(
            email="user@test.com",
            password="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_update_delete_forbidden_books(self) -> None:
        # create
        payload = {
            "title": "Book title",
            "author": "Author Sample",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": Decimal("1.04")
        }

        res_create = self.client.post(BOOK_URL, payload)

        self.assertEqual(res_create.status_code, status.HTTP_403_FORBIDDEN)

        book = sample_book()

        # update
        url_update = get_detail(book.id)
        res_update = self.client.put(url_update, {"title": "test title"})
        self.assertEqual(res_update.status_code, status.HTTP_403_FORBIDDEN)

        # delete
        url_delete = get_detail(book.id)
        res_delete = self.client.delete(url_delete)
        self.assertEqual(res_delete.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookAPITests(TestCase):
    def setUp(self) -> None:
        self.payload = {
            "title": "Book title",
            "author": "Author Sample",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": Decimal("1.04")
        }
        self.user = get_user_model().objects.create_superuser(
            email="user@test.com",
            password="test"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        res = self.client.post(BOOK_URL, self.payload)
        book = Book.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in self.payload:
            self.assertEqual(self.payload[key], getattr(book, key))

    def test_update_book(self):
        self.payload["title"] = "Book title put"
        book = sample_book()

        url = get_detail(book.id)

        res = self.client.put(url, self.payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_book(self):
        book = sample_book()

        url = get_detail(book.id)

        res = self.client.delete(url, self.payload)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(book, Book.objects.all())
