from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from datetime import date, timedelta, datetime

BORROWINGS_URL = reverse("borrowings:borrowings-list")


def get_detail(borrowings_id: int) -> str:
    return reverse("borrowings:borrowings-detail", args=[borrowings_id])


class BorrowingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="password"
        )
        self.book = Book.objects.create(
            title="Book title",
            author="Author Sample",
            cover="SOFT",
            inventory=10,
            daily_fee=Decimal("1.04")
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_borrowing(self):
        data = {
            "book": self.book.id,
            "expected_return_date": (date.today() +
                                     timedelta(days=7)).isoformat(),
        }
        response = self.client.post(BORROWINGS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertEqual(Borrowing.objects.first().user, self.user)

    def test_list_borrowings(self):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_borrowing_detail(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        response = self.client.get(get_detail(borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    def test_return_borrowing(self):
        borrowing = Borrowing.objects.create(
            user=self.user, book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        data = {
            "actual_return_date": date.today().isoformat(),
        }
        response = self.client.patch(get_detail(borrowing.id), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, date.today())

    def test_inventory_decrease_on_borrow(self):
        initial_inventory = self.book.inventory
        self.borrowing_data = {
            "book": self.book.id,
            "expected_return_date": (
                        date.today() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(
            BORROWINGS_URL,
            self.borrowing_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)
