"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import auth views
from .auth_views import RegisterView, LoginView, UserProfileView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Authentication endpoints
    path("api/auth/register/", RegisterView.as_view(), name='register'),
    path("api/auth/login/", LoginView.as_view(), name='login'),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("api/auth/user/", UserProfileView.as_view(), name='user_profile'),
    
    # API endpoints - enable them one by one as they're ready
    path("api/", include("people.urls")),
    path("api/", include("tasks.urls")),
    path("api/", include("ai_integration.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)