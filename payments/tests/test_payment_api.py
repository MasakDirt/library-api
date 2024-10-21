import datetime
from dataclasses import dataclass
from unittest.mock import patch, AsyncMock

import stripe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import (
    PaymentListSerializer,
    PaymentRetrieveSerializer,
)
from payments.views import PaymentViewSet


PAYMENT_URL = reverse("payments:payment-list")

User = get_user_model()


def get_detail(payment_id: int) -> str:
    return reverse("payments:payment-detail", args=[payment_id])


def get_success(payment_id: int) -> str:
    return reverse("payments:payment-success", args=[payment_id])


def get_cancel(payment_id: int) -> str:
    return reverse("payments:payment-cancel", args=[payment_id])


@dataclass
class SessionStripe:
    id: str
    url: str


@dataclass
class CustomerDetailsTest:
    name: str
    email: str


@dataclass
class SuccessSessionTest:
    customer_details: CustomerDetailsTest


class PaymentAPITests(TestCase):

    @patch("stripe.checkout.Session.create")
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def setUp(self, mocked_notify, mock_create_session):
        mock_create_session.return_value = SessionStripe(
            id="fake_session_id",
            url="https://fake-stripe-url.com"
        )

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="test1234"
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="test1234"
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            cover="HARD",
            inventory=10,
            daily_fee=5.00,
        )
        self.borrowing1 = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date="2024-10-01",
            expected_return_date="2024-10-10",
        )
        self.borrowing2 = Borrowing.objects.create(
            book=self.book,
            user=self.admin_user,
            borrow_date="2023-10-01",
            expected_return_date="2023-10-10",
        )

    def test_list_payments_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(PAYMENT_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_payments_admin(self):

        self.client.force_authenticate(self.admin_user)
        response = self.client.get(PAYMENT_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)


class PaymentViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com",
            password="test1234"
        )
        self.client.force_authenticate(self.user)
        self.view = PaymentViewSet()

    def test_list_action_uses_correct_serializer(self):
        self.view.action = "list"
        serializer_class = self.view.get_serializer_class()

        self.assertEqual(serializer_class, PaymentListSerializer)

    def test_retrieve_action_uses_correct_serializer(self):
        self.view.action = "retrieve"
        serializer_class = self.view.get_serializer_class()

        self.assertEqual(serializer_class, PaymentRetrieveSerializer)


class PaymentSuccessCancelTests(TestCase):
    @patch("stripe.checkout.Session.create")
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def setUp(self, mocked_notify, mock_create_session):
        mock_create_session.return_value = SessionStripe(
            id="fake_session_id",
            url="https://fake-stripe-url.com"
        )

        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            cover="HARD",
            inventory=10,
            daily_fee=5.00,
        )

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=datetime.date(2024, 12, 12),
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_id="test_session_id",
            status="PAID",
            money_to_pay=2000
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @patch("stripe.checkout.Session.retrieve")
    def test_payment_success(self, mock_stripe_retrieve):
        mock_stripe_retrieve.return_value = SuccessSessionTest(
            CustomerDetailsTest(name="Maks", email="test@test.com")
        )

        response = self.client.get(get_success(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["customer"]["name"], "Maks")
        self.assertEqual(response.data["customer"]["email"], "test@test.com")
        self.assertIn("Thanks for your order", response.data["detail"])

    @patch("stripe.checkout.Session.retrieve")
    def test_payment_success_no_session(self, mock_stripe_retrieve):
        self.payment.session_id = None
        self.payment.save()

        response = self.client.get(get_success(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Session ID is required")

    @patch("stripe.checkout.Session.retrieve")
    def test_payment_success_stripe_error(self, mock_stripe_retrieve):
        mock_stripe_retrieve.side_effect = stripe.error.StripeError(
            "Some error occurred"
        )

        response = self.client.get(get_success(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Some error occurred")


class PaymentCancelTests(TestCase):
    @patch("stripe.checkout.Session.create")
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    def setUp(self, mocked_notify, mock_create_session):
        mock_create_session.return_value = SessionStripe(
            id="fake_session_id",
            url="https://fake-stripe-url.com"
        )

        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            cover="HARD",
            inventory=10,
            daily_fee=5.00,
        )

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=datetime.date(2024, 12, 12),
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_id="test_session_id",
            status="PENDING",
            money_to_pay=2000
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_payment_cancel_pending(self):
        response = self.client.get(get_cancel(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["payment"]["session_id"],
            "test_session_id"
        )
        self.assertIn("Okay,", response.data["detail"])

    def test_payment_cancel_paid(self):
        self.payment.status = "PAID"
        self.payment.save()

        response = self.client.get(get_cancel(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            f"Dear '{self.user.email}', you have already "
            f"paid this borrowing!",
            response.data["detail"]
        )

    def test_payment_cancel_forbidden(self):
        other_user = User.objects.create_user(
            email="otheruser@email.co",
            password="password123"
        )
        self.client.force_authenticate(other_user)

        response = self.client.get(get_cancel(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "It`s not your payment! Be more attentive!"
        )

    def test_payment_cancel_no_session(self):
        self.payment.session_id = None
        self.payment.save()

        response = self.client.get(get_cancel(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Session ID is required")
