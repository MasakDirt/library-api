from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer

from books.filters import CustomBookSearchFilter
from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import (
    BookSerializer,
    BookListSerializer,
    BookRetrieveSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (CustomBookSearchFilter,)

    def get_serializer_class(self) -> ModelSerializer:
        serializer = super().get_serializer_class()

        if self.action == "list":
            serializer = BookListSerializer

        if self.action == "retrieve":
            serializer = BookRetrieveSerializer

        return serializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="title",
                type=str,
                description="Find book with this title",
                enum=["Study", "St", "Free"]
            ),
            OpenApiParameter(
                name="author",
                type=str,
                description="Find book with this author",
                enum=["peter", "Ma"]
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List of books with pagination and searching"""
        return super().list(request, *args, **kwargs)
