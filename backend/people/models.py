from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from bson import ObjectId
import datetime

# Django ORM User model for authentication
class User(AbstractUser):
    """
    Custom Django ORM User model to satisfy Django's authentication requirements.
    The actual user data is stored in MongoDB and this model acts as a bridge.
    """
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def is_admin(self):
        """Check if user has admin role"""
        # Find the MongoDB user with the same username
        mongo_user = users_collection.find_one({'username': self.username})
        if mongo_user and 'role' in mongo_user:
            role_id = mongo_user['role']
            if isinstance(role_id, str):
                try:
                    role_id = ObjectId(role_id)
                except:
                    return False
            
            role = roles_collection.find_one({'_id': role_id})
            return role and role.get('permission_level', 0) >= 4
        return self.is_superuser
    
    def is_manager(self):
        """Check if user has manager role"""
        # Find the MongoDB user with the same username
        mongo_user = users_collection.find_one({'username': self.username})
        if mongo_user and 'role' in mongo_user:
            role_id = mongo_user['role']
            if isinstance(role_id, str):
                try:
                    role_id = ObjectId(role_id)
                except:
                    return False
                    
            role = roles_collection.find_one({'_id': role_id})
            return role and role.get('permission_level', 0) >= 3
        return self.is_superuser
    
    def save(self, *args, **kwargs):
        """
        Override save to sync with MongoDB
        """
        # Call the Django ORM save
        super().save(*args, **kwargs)
        
        # Sync with MongoDB - upsert the user
        mongo_data = {
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'updated_at': datetime.datetime.now()
        }
        
        # Don't include password if it hasn't been set yet
        if self.password:
            mongo_data['password'] = self.password
            
        # Upsert to MongoDB
        users_collection.update_one(
            {'username': self.username},
            {'$set': mongo_data},
            upsert=True
        )


# Access MongoDB collections
users_collection = settings.MONGODB_DB['users']
roles_collection = settings.MONGODB_DB['roles'] 
teams_collection = settings.MONGODB_DB['teams']

# PyMongo implementation for direct MongoDB access
class MongoUser:
    """
    Implementation of User model using pymongo directly
    """
    
    @staticmethod
    def create(user_data):
        """Create a new user"""
        # Handle password hashing if needed
        if 'password' in user_data and user_data['password']:
            from django.contrib.auth.hashers import make_password
            user_data['password'] = make_password(user_data['password'])
            
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.datetime.now()
            
        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        # Create Django user for authentication
        try:
            User.objects.create_user(
                username=user_data.get('username', ''),
                email=user_data.get('email', ''),
                password=user_data.get('password', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', '')
            )
        except Exception as e:
            print(f"Error creating Django user: {e}")
            
        return user_data
    
    @staticmethod
    def get_by_id(user_id):
        """Get a user by ID"""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return None
                
        return users_collection.find_one({'_id': user_id})
    
    @staticmethod
    def get_by_username(username):
        """Get a user by username"""
        return users_collection.find_one({'username': username})
    
    @staticmethod
    def get_all():
        """Get all users"""
        return list(users_collection.find())
    
    @staticmethod
    def update(user_id, update_data):
        """Update a user"""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return None
        
        # Handle password updates
        if 'password' in update_data and update_data['password']:
            from django.contrib.auth.hashers import make_password
            update_data['password'] = make_password(update_data['password'])
        
        # Add updated timestamp
        update_data['updated_at'] = datetime.datetime.now()
        
        result = users_collection.update_one(
            {'_id': user_id},
            {'$set': update_data}
        )
        
        # Update Django User if username is available
        user = users_collection.find_one({'_id': user_id})
        if user and 'username' in user:
            try:
                django_user = User.objects.get(username=user['username'])
                if 'email' in update_data:
                    django_user.email = update_data['email']
                if 'first_name' in update_data:
                    django_user.first_name = update_data['first_name']
                if 'last_name' in update_data:
                    django_user.last_name = update_data['last_name']
                if 'password' in update_data:
                    django_user.password = update_data['password']
                django_user.save()
            except User.DoesNotExist:
                pass
        
        if result.modified_count > 0:
            return MongoUser.get_by_id(user_id)
        return None


class Role:
    """
    Implementation of Role model using pymongo directly
    """
    
    @staticmethod
    def create(data):
        """Create a new role"""
        result = roles_collection.insert_one(data)
        data['_id'] = result.inserted_id
        return data
    
    @staticmethod
    def get_by_id(role_id):
        """Get a role by ID"""
        if isinstance(role_id, str):
            try:
                role_id = ObjectId(role_id)
            except:
                return None
                
        return roles_collection.find_one({'_id': role_id})
    
    @staticmethod
    def get_all():
        """Get all roles"""
        return list(roles_collection.find())


class Team:
    """
    Implementation of Team model using pymongo directly
    """
    
    @staticmethod
    def create(team_data):
        """Create a new team"""
        if 'created_at' not in team_data:
            team_data['created_at'] = datetime.datetime.now()
            
        result = teams_collection.insert_one(team_data)
        team_data['_id'] = result.inserted_id
        return team_data
    
    @staticmethod
    def get_by_id(team_id):
        """Get a team by ID"""
        if isinstance(team_id, str):
            try:
                team_id = ObjectId(team_id)
            except:
                return None
                
        return teams_collection.find_one({'_id': team_id})
    
    @staticmethod
    def get_all():
        """Get all teams"""
        return list(teams_collection.find())
    
    @staticmethod
    def update(team_id, update_data):
        """Update a team"""
        if isinstance(team_id, str):
            try:
                team_id = ObjectId(team_id)
            except:
                return None
                
        result = teams_collection.update_one(
            {'_id': team_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return Team.get_by_id(team_id)
        return None
    
    @staticmethod
    def add_member(team_id, user_id):
        """Add a user to a team"""
        if isinstance(team_id, str):
            try:
                team_id = ObjectId(team_id)
            except:
                return False
                
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return False
                
        result = teams_collection.update_one(
            {'_id': team_id},
            {'$addToSet': {'members': user_id}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def remove_member(team_id, user_id):
        """Remove a user from a team"""
        if isinstance(team_id, str):
            try:
                team_id = ObjectId(team_id)
            except:
                return False
                
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return False
                
        result = teams_collection.update_one(
            {'_id': team_id},
            {'$pull': {'members': user_id}}
        )
        
        return result.modified_count > 0