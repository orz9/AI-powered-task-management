from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .auth_views import RegisterView, LoginView, UserProfileView

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/', UserProfileView.as_view(), name='user_profile'),
]