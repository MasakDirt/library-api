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

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        elif user_id and self.request.user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        if is_active:
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset


    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            if not self.request.user.is_staff:
                return BorrowingReadAuthenticatedSerializer
            return BorrowingReadSerializer
        return BorrowingCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
