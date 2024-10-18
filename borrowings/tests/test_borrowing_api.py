from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing


BORROWINGS_URL = reverse("borrowings:borrowings-list")


def get_detail(borrowings_id: int) -> str:
    return reverse("borrowings:borrowings-detail", args=[borrowings_id])


def get_return_url(borrowings_id: int) -> str:
    return reverse("borrowings:borrowings-return-borrowings", args=[borrowings_id])


def sample_user(email, password):
    return get_user_model().objects.create_user(email, password)


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


def sample_borrowing(user, book):
    return Borrowing.objects.create(
        user=user,
        book=book,
        expected_return_date=date.today() + timedelta(days=7)
    )


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

    @patch("borrowings.signals.notify_borrowing_create")
    def test_create_borrowing(self, mocked_notify):
        data = {
            "book": self.book.id,
            "expected_return_date": (date.today() +
                                     timedelta(days=7)).isoformat(),
        }
        response = self.client.post(BORROWINGS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        self.assertEqual(Borrowing.objects.first().user, self.user)

    @patch("borrowings.signals.notify_borrowing_create")
    def test_list_borrowings(self, mocked_notify):
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("borrowings.signals.notify_borrowing_create")
    def test_borrowing_detail(self, mocked_notify):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        response = self.client.get(get_detail(borrowing.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    @patch("borrowings.signals.notify_borrowing_create")
    def test_return_borrowing(self, mocked_notify):
        borrowing = Borrowing.objects.create(
            user=self.user, book=self.book,
            expected_return_date=date.today() + timedelta(days=7)
        )

        data = {
            "actual_return_date": date.today().isoformat(),
        }
        response = self.client.patch(
            get_detail(borrowing.id),
            data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, date.today())

    @patch("borrowings.signals.notify_borrowing_create")
    def test_inventory_decrease_on_borrow(self, mocked_notify):
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


class UnAuthenticatedBorrowingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_borrowings_forbidden(self):
        response = self.client.get(BORROWINGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingTests(TestCase):
    @patch("borrowings.signals.notify_borrowing_create")
    def setUp(self, mocked_notify):
        self.user = sample_user(
            email="test@test.com",
            password="password"
        )
        self.user_2 = sample_user(
            email="test1@test1.com",
            password="password"
        )
        self.book = sample_book()

        sample_borrowing(user=self.user, book=self.book)
        sample_borrowing(user=self.user_2, book=self.book)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_user_borrowings(self):
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0].get("user", None), None)

    def test_retrieve_user_borrowings(self):
        response = self.client.get(get_detail(self.user.id))
        response_not_found = self.client.get(get_detail(self.user_2.id))

        self.assertEqual(
            response_not_found.status_code,
            status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.data.get("user"))

    @patch("borrowings.signals.notify_borrowing_create")
    def test_create_user_borrowings_and_notification_send(self, mocked_notify):
        payload = {
            "book": self.book.id,
            "expected_return_date": date(2024, 12, 10),
            "actual_return_date": date(2024, 12, 1),
        }
        response = self.client.post(
            BORROWINGS_URL,
            data=payload,
            format="json"
        )

        borrowing = Borrowing.objects.get(pk=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["book"], borrowing.book.id)
        self.assertEqual(
            payload["expected_return_date"],
            borrowing.expected_return_date
        )
        self.assertEqual(
            payload["actual_return_date"],
            borrowing.actual_return_date
        )
        self.assertTrue(mocked_notify.called)


class AdminBorrowingTests(TestCase):
    @patch("borrowings.signals.notify_borrowing_create")
    def setUp(self, mocked_notify):
        self.user = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="password"
        )
        self.user_2 = sample_user(
            email="test1@test1.com",
            password="password"
        )
        self.book = sample_book()

        sample_borrowing(user=self.user, book=self.book)
        sample_borrowing(user=self.user_2, book=self.book)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_user_borrowings(self):
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_user_borrowings(self):
        response = self.client.get(get_detail(self.user_2.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("borrowings.signals.notify_borrowing_create")
    def test_list_filter_is_active_borrowings(self, mocked_notify):
        Borrowing.objects.create(
            user=self.user_2,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=date.today()
        )

        response = self.client.get(BORROWINGS_URL, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_filter_user_id_borrowings(self):
        response = self.client.get(BORROWINGS_URL, {"user_id": self.user_2.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            Borrowing.objects.filter(user_id=self.user_2.id).count()
        )


class ReturnBorrowingsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="password"
        )
        self.user_2 = sample_user(
            email="test1@test1.com",
            password="password"
        )
        self.book = sample_book()
        self.borrowing= sample_borrowing(user=self.user, book=self.book)
        self.borrowing_user_2 = sample_borrowing(user=self.user_2, book=self.book)
        self.client = APIClient()
        self.client.force_authenticate(self.user_2)

    def test_return_borrowings(self):
        book_inventory = self.book.inventory
        response = self.client.post(get_return_url(self.borrowing_user_2.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["actual_return_date"], str(date.today()))

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, book_inventory + 1)

    def test_return_borrowings_forbidden(self):
        response = self.client.post(get_return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_already_returned_borrowings(self):
        self.client.post(get_return_url(self.borrowing_user_2.id))

        response = self.client.post(get_return_url(self.borrowing_user_2.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
