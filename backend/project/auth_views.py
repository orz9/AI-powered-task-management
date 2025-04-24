from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from bson import ObjectId
import datetime
from rest_framework_simplejwt.tokens import RefreshToken
import logging

# Basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

User = get_user_model()

# Access MongoDB collections
users_collection = settings.MONGODB_DB['users']
roles_collection = settings.MONGODB_DB['roles']

class RegisterView(APIView):
    """
    API endpoint for user registration
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data['username']
            email = request.data['email']
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            
            # Check MongoDB first
            mongo_user = users_collection.find_one({'username': username})
            if mongo_user:
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if users_collection.find_one({'email': email}):
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user exists in Django but not in MongoDB
            django_user_exists = User.objects.filter(username=username).exists()
            
            # Get role information
            is_admin = request.data.get('is_admin', False)
            if isinstance(is_admin, str):
                is_admin = is_admin.lower() == 'true'
                
            role_name = 'admin' if is_admin else 'team_member'
        
            # Get or create appropriate role in MongoDB
            role = roles_collection.find_one({'name': role_name})
            if not role:
                role_data = {
                    'name': role_name,
                    'description': f'{role_name.capitalize()} role',
                    'permission_level': 4 if role_name == 'admin' else 1
                }
                role_result = roles_collection.insert_one(role_data)
                role_id = role_result.inserted_id
            else:
                role_id = role['_id']
        
            # Create MongoDB user with role
            from django.contrib.auth.hashers import make_password
            mongo_data = {
                'username': username,
                'email': email,
                'password': make_password(request.data['password']),
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'is_staff': is_admin,
                'is_superuser': is_admin,
                'role': role_id,
                'created_at': datetime.datetime.now(),
                'updated_at': datetime.datetime.now()
            }
        
            # Insert into MongoDB
            result = users_collection.insert_one(mongo_data)
        
            # Prepare person name (use username if both first and last names are empty)
            person_name = f"{first_name} {last_name}".strip() or username
            
            # Create person record linked to this user
            person_data = {
                'userId': result.inserted_id,
                'name': person_name,
                'email': email,
                'role': role_name,
                'teams': [],
                'skills': [],
                'organization': ObjectId("000000000000000000000001"),  # Default organization ID
                'created_at': datetime.datetime.now()
            }
        
            # Add person to people collection
            people_collection = settings.MONGODB_DB['people']
            person_result = people_collection.insert_one(person_data)
            
            # Create or get Django user for authentication
            if django_user_exists:
                django_user = User.objects.get(username=username)
                # Update password if it changed
                django_user.set_password(request.data['password'])
                # Update other fields
                django_user.email = email
                django_user.first_name = first_name
                django_user.last_name = last_name
            else:
                django_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=request.data['password'],
                    first_name=first_name,
                    last_name=last_name
                )
            
            # Set staff and superuser status if admin
            if is_admin:
                django_user.is_staff = True
                django_user.is_superuser = True
            
            django_user.save()
            
            # Generate JWT token
            refresh = RefreshToken.for_user(django_user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # Prepare response data
            response_data = {
                'user': {
                    'id': str(result.inserted_id),
                    'username': mongo_data['username'],
                    'email': mongo_data['email'],
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role_name
                },
                'token': tokens['access']
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Creating a logger
            logger = logging.getLogger(__name__)
            logger.error(f"Registration failed: {str(e)}")
            # Print stack trace for debugging
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """
    API endpoint for user login
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {"error": "Username and password are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Authenticate user (this will use our custom auth backend)
            from django.contrib.auth import authenticate
            user = authenticate(request, username=username, password=password)
            
            if not user:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # Get MongoDB user data for additional info
            mongo_user = users_collection.find_one({'username': username})
            role_name = None
            
            if mongo_user and 'role' in mongo_user and mongo_user['role']:
                role = roles_collection.find_one({'_id': mongo_user['role']})
                if role:
                    role_name = role.get('name')
            
            # Prepare response data
            response_data = {
                'user': {
                    'id': str(mongo_user['_id']) if mongo_user else str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': role_name
                },
                'token': tokens['access']
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {"error": f"Login failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    """
    API endpoint for getting and updating user profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get MongoDB user data for complete profile
            mongo_user = users_collection.find_one({'username': request.user.username})
            
            if not mongo_user:
                return Response(
                    {"error": "User not found in MongoDB"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get role info if available
            role_name = None
            if 'role' in mongo_user and mongo_user['role']:
                role = roles_collection.find_one({'_id': mongo_user['role']})
                if role:
                    role_name = role.get('name')
            
            # Prepare response data
            user_data = {
                'id': str(mongo_user['_id']),
                'username': mongo_user['username'],
                'email': mongo_user['email'],
                'first_name': mongo_user.get('first_name', ''),
                'last_name': mongo_user.get('last_name', ''),
                'role': role_name,
                'profile_picture': mongo_user.get('profile_picture', None),
                'bio': mongo_user.get('bio', '')
            }
            
            return Response(user_data)
            
        except Exception as e:
            return Response(
                {"error": f"Error retrieving user profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        try:
            # Get user data
            user = request.user
            mongo_user = users_collection.find_one({'username': user.username})
            
            if not mongo_user:
                return Response(
                    {"error": "User not found in MongoDB"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Fields that can be updated
            allowed_fields = ['_id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role']
            update_data = {}
            
            # Validate and prepare update data
            for field in allowed_fields:
                if field in request.data:
                    update_data[field] = request.data[field]
            
            update_data['_id'] = ObjectId(update_data['_id'])
            
            role_name = update_data['role']
            if 'role' in allowed_fields and update_data['role']:
                update_data['role'] = roles_collection.find_one({'name': update_data['role']}).get('_id')
            
            # Update Django user
            if 'email' in update_data:
                user.email = update_data['email']
            if 'first_name' in update_data:
                user.first_name = update_data['first_name']
            if 'last_name' in update_data:
                user.last_name = update_data['last_name']
            
            user.save()
            
            # Update MongoDB user
            update_data['updated_at'] = datetime.datetime.now()
            users_collection.update_one(
                {'_id': mongo_user['_id']},
                {'$set': update_data}
            )
            
            # Get updated user data
            updated_user = users_collection.find_one({'_id': mongo_user['_id']})
            
            # Create person record linked to this user
            person_data = {
                'name': updated_user['first_name'] + ' ' + updated_user['username'],
                'email': updated_user['email'],
                'role': role_name
            }
        
            # Add person to people collection
            people_collection = settings.MONGODB_DB['people']
            people_collection.update_one(
                {'userId': updated_user['_id']},
                {'$set': person_data}
            )
            
            # Prepare response data
            response_data = {
                'bio': '',
                'id': str(updated_user['_id']),
                'username': updated_user['username'],
                'email': updated_user['email'],
                'first_name': updated_user['first_name'],
                'last_name': updated_user['last_name'],
                'role': role_name,
                'profile_picture': None
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {"error": f"Error updating user profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )