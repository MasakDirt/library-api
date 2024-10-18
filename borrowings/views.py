from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Borrowing
from .serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer,
    BorrowingReadAuthenticatedSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user")
    permission_classes = (IsAuthenticated,)
    serializer_class = BorrowingCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif user_id and user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        if is_active and is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    def get_serializer_class(self):
        serializer = super().get_serializer_class()
        if self.action in ["list", "retrieve"]:
            if not self.request.user.is_staff:
                return BorrowingReadAuthenticatedSerializer
            serializer = BorrowingReadSerializer
        return serializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
