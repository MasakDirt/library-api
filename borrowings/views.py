from rest_framework import status
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from django.db import transaction
from datetime import date

from common.serializers import BorrowingListRetrieveSerializer
from payments.utils import create_payment_with_session
from .models import Borrowing
from .serializers import (
    BorrowingSerializer,
    BorrowingRetrieveAdminSerializer,
    BorrowingListSerializer,
    BorrowingListAdminSerializer,
    BorrowingRetrieveSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        user = self.request.user

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("payments")

        if not user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif user_id and user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        if is_active and is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    def get_serializer_class(self):
        serializer = super().get_serializer_class()
        if self.action == "list":
            if not self.request.user.is_staff:
                return BorrowingListSerializer
            serializer = BorrowingListAdminSerializer
        if self.action == "retrieve":
            if not self.request.user.is_staff:
                return BorrowingRetrieveAdminSerializer
            serializer = BorrowingRetrieveSerializer

        if self.action == "return_borrowings":
            serializer = BorrowingListRetrieveSerializer
        return serializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)

    @action(
        methods=["POST"],
        detail=True,
        url_path="return-borrowings",
        url_name="return-borrowings",
    )
    def return_borrowing(self, request: Request, pk: int = None) -> Response:
        """Endpoint for returning borrowing"""
        borrowing = get_object_or_404(Borrowing, pk=pk)

        if borrowing.actual_return_date:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if borrowing.user_id != self.request.user.id:
            return Response(
                {"detail": "This is not your borrowing."},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            borrowing.book.inventory += 1
            borrowing.book.save()

            borrowing.actual_return_date = date.today()
            borrowing.save()

            if (
                borrowing.actual_return_date - borrowing.expected_return_date
            ).days > 0:
                create_payment_with_session(borrowing, borrowing_type="Fine")

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=bool,
                description="Find borrowings which have not returned yet",
                enum=["true", "false"]
            ),
            OpenApiParameter(
                name="user_id",
                type=int,
                description="Only admin feature, find borrowings by user id",
                enum=[1, 3, 4]
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List of borrowings (user - get only his borrowings),
         (admin can check all borrowings)"""
        return super().list(request, *args, **kwargs)
