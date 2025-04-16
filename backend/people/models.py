from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Role(models.Model):
    """
    Role model defines the various roles users can have in the system.
    Each role has specific permissions and UI views.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Permission levels (higher number = more permissions)
    permission_level = models.IntegerField(default=1)
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Extended User model that includes additional fields necessary for our system.
    """
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.username

    def is_admin(self):
        """Check if user has admin role"""
        return self.role and self.role.permission_level >= 4
    
    def is_manager(self):
        """Check if user has manager role"""
        return self.role and self.role.permission_level >= 3


class Team(models.Model):
    """
    Team model for grouping users working together on projects.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                              null=True, related_name='led_teams')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name