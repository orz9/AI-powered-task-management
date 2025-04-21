import os
import django
import pymongo
from django.contrib.auth.hashers import make_password
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def create_superuser():
    # User details
    username = 'admin'
    email = 'admin@example.com'
    password = 'adminpassword123'
    
    # Create Django User
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"Django superuser '{username}' created successfully!")
    except Exception as e:
        print(f"Error creating Django superuser: {e}")
        user = User.objects.get(username=username)
        print(f"Using existing Django superuser '{username}'")
    
    # Create MongoDB User
    users_collection = settings.MONGODB_DB['users']
    
    # Check if MongoDB user exists
    existing_user = users_collection.find_one({'username': username})
    
    if existing_user:
        print(f"MongoDB user '{username}' already exists")
    else:
        # Create MongoDB user
        user_data = {
            'username': username,
            'email': email,
            'password': make_password(password),
            'first_name': 'Admin',
            'last_name': 'User',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = users_collection.insert_one(user_data)
        print(f"MongoDB superuser '{username}' created with ID: {result.inserted_id}")
    
    print("Superuser creation completed")

if __name__ == '__main__':
    create_superuser()