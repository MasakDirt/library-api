from rest_framework import serializers

from books.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")


class BookRetrieveSerializer(BookSerializer):
    cover = serializers.SerializerMethodField()

    def get_cover(self, obj: Book) -> str:
        return obj.get_cover_display()


class BookListSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover")

    def get_cover(self, obj: Book) -> str:
        return obj.get_cover_display()
