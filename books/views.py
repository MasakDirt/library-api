from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer, BookListSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_serializer_class(self) -> ModelSerializer:
        serializer = self.serializer_class

        if self.action == "list":
            serializer = BookListSerializer

        return serializer
