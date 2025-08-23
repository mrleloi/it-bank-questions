"""Django REST Framework URLs."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    QuestionViewSet,
    SessionViewSet,
    ProgressViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'sessions', SessionViewSet)
router.register(r'progress', ProgressViewSet)

urlpatterns = [
    path('admin/api/', include(router.urls)),
]