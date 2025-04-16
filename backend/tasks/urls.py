from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, CommentViewSet, AttachmentViewSet, 
    TaskCategoryViewSet, SecurityLevelViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'attachments', AttachmentViewSet)
router.register(r'categories', TaskCategoryViewSet)
router.register(r'security-levels', SecurityLevelViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]