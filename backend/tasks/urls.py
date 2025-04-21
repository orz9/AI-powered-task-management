from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, CommentViewSet, AttachmentViewSet, 
    TaskCategoryViewSet, SecurityLevelViewSet
)

# Create a router and register our viewsets with explicit basenames
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'categories', TaskCategoryViewSet, basename='category')
router.register(r'security-levels', SecurityLevelViewSet, basename='security-level')

# The API URLs are now determined automatically by the router
urlpatterns = router.urls