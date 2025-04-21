from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.conf import settings
from bson import ObjectId

User = get_user_model()

class MongoDBAuthBackend(ModelBackend):
    """
    Custom authentication backend that validates against MongoDB users
    but still uses Django's User model for authentication framework
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First try to find the user in MongoDB
        users_collection = settings.MONGODB_DB['users']
        mongo_user = users_collection.find_one({'username': username})
        
        if not mongo_user:
            return None
            
        # Check password
        if not check_password(password, mongo_user.get('password', '')):
            return None
            
        # Get or create Django user model instance
        try:
            django_user = User.objects.get(username=username)
            # Update Django user with MongoDB data
            django_user.email = mongo_user.get('email', '')
            django_user.first_name = mongo_user.get('first_name', '')
            django_user.last_name = mongo_user.get('last_name', '')
            django_user.is_staff = mongo_user.get('is_staff', False)
            django_user.is_superuser = mongo_user.get('is_superuser', False)
            django_user.save()
        except User.DoesNotExist:
            # Create new Django user
            django_user = User.objects.create_user(
                username=username,
                email=mongo_user.get('email', ''),
                first_name=mongo_user.get('first_name', ''),
                last_name=mongo_user.get('last_name', '')
            )
            # Set is_staff and is_superuser
            django_user.is_staff = mongo_user.get('is_staff', False) 
            django_user.is_superuser = mongo_user.get('is_superuser', False)
            django_user.save()
            
        return django_user