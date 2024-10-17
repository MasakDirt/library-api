from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BorrowingViewSet

app_name = "borrowings"
router = DefaultRouter()

router.register("borrowings", BorrowingViewSet, basename="borrowings")

urlpatterns = [
    path("", include(router.urls))
]
