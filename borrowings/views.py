from typing import Type

from rest_framework import viewsets

from .models import Borrowing
from .serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user")

    def get_serializer_class(self) -> Type[
        BorrowingReadSerializer | BorrowingCreateSerializer
        ]:
        if self.action in ["list", "retrieve"]:
            return BorrowingReadSerializer
        return BorrowingCreateSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
