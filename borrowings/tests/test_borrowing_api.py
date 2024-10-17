from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from books.models import Book
from borrowings.models import Borrowing
from datetime import date, timedelta

class BorrowingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password"
        )
        self.book = Book.objects.create(title="Test Book", inventory=5)

    def test_create_borrowing(self):
        url = reverse("borrowings-list")
        data = {
            "book": self.book.id,
            "expected_return_date": (date.today() +
                                     timedelta(days=7)).isoformat(),
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertEqual(Borrowing.objects.first().user, self.user)

    def test_list_borrowings(self):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )
        url = reverse("borrowings-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_borrowing_detail(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )
        url = reverse("borrowings-detail", args=[borrowing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    def test_return_borrowing(self):
        borrowing = Borrowing.objects.create(
            user=self.user, book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )
        url = reverse("borrowings-detail", args=[borrowing.id])
        data = {
            "actual_return_date": date.today().isoformat(),
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, date.today())

    def test_inventory_decrease_on_borrow(self):
        initial_inventory = self.book.inventory
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

    def test_inventory_increase_on_return(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )
        borrowing.actual_return_date = date.today()
        borrowing.save()
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)
