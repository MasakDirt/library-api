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
    PaymentRetrieveSerializer
)
from payments.views import PaymentViewSet


PAYMENT_URL = reverse("payments:payment-list")

User = get_user_model()


def get_detail(payment_id: int) -> str:
    return reverse("payments:payment-detail", args=[payment_id])


class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com",
            password="test1234"
        )
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="test1234"
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            cover="HARD",
            inventory=10,
            daily_fee=5.00
        )
        self.borrowing1 = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date="2024-10-01",
            expected_return_date="2024-10-10"
        )
        self.borrowing2 = Borrowing.objects.create(
            book=self.book,
            user=self.admin_user,
            borrow_date="2023-10-01",
            expected_return_date="2023-10-10"
        )

        self.payment1 = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowing=self.borrowing1,
            session_url="https://stripe.com/payment/1",
            session_id="session_1",
            money_to_pay=50.00
        )
        self.payment2 = Payment.objects.create(
            status="PAID",
            type="FINE",
            borrowing=self.borrowing2,
            session_url="https://stripe.com/payment/2",
            session_id="session_2",
            money_to_pay=10.00
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
