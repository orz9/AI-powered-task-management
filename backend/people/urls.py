from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TeamViewSet, RoleViewSet, TeamAssignmentView, PeopleListView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'roles', RoleViewSet, basename='role')

# Additional URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('teams/assign/', TeamAssignmentView.as_view(), name='team-assign'),
    path('people/', PeopleListView.as_view(), name='people-list'),
]