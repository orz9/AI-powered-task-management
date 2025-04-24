from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from bson import ObjectId
import datetime
import logging

from .permissions import IsAdminOrManager, IsSelfOrAdmin

# Get MongoDB collections
users_collection = settings.MONGODB_DB['users']
roles_collection = settings.MONGODB_DB['roles']
teams_collection = settings.MONGODB_DB['teams']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def convert_objectids(obj):
    for key in obj:
        if isinstance(obj[key], ObjectId):
            obj[key] = str(obj[key])
    return obj
    
class UserViewSet(viewsets.ViewSet):
    """
    API endpoint for user management
    """
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSelfOrAdmin]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all users"""
        users = list(users_collection.find())
        
        # Convert ObjectId to string for serialization
        for user in users:
            user['_id'] = str(user['_id'])
            if 'role' in user and user['role'] and isinstance(user['role'], ObjectId):
                user['role'] = str(user['role'])
        
        return Response(users)
    
    def retrieve(self, request, pk=None):
        """Get a specific user"""
        try:
            user_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = users_collection.find_one({'_id': user_id})
        
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert ObjectId to string for serialization
        user['_id'] = str(user['_id'])
        if 'role' in user and user['role'] and isinstance(user['role'], ObjectId):
            user['role'] = str(user['role'])
        
        return Response(user)
    
    def create(self, request):
        """Create a new user""" 
        # Add created_at timestamp
        user_data = request.data
        user_data['created_at'] = datetime.datetime.now()
        
        # Hash password if provided
        if 'password' in user_data:
            from django.contrib.auth.hashers import make_password
            user_data['password'] = make_password(user_data['password'])
        
        # Convert role ID to ObjectId if provided
        if 'role' in user_data and user_data['role']:
            try:
                user_data['role'] = ObjectId(user_data['role'])
            except:
                return Response({"error": "Invalid role ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Insert into MongoDB
        result = users_collection.insert_one(user_data)
        
        # Get the created user
        created_user = users_collection.find_one({'_id': result.inserted_id})
        created_user['_id'] = str(created_user['_id'])
        
        return Response(created_user, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update a user"""
        try:
            user_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = users_collection.find_one({'_id': user_id})
        
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        update_data = request.data
        
        # Hash password if being updated
        if 'password' in update_data:
            from django.contrib.auth.hashers import make_password
            update_data['password'] = make_password(update_data['password'])
        
        # Convert role ID to ObjectId if provided
        if 'role' in update_data and update_data['role']:
            try:
                update_data['role'] = ObjectId(update_data['role'])
            except:
                return Response({"error": "Invalid role ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Add updated_at timestamp
        update_data['updated_at'] = datetime.datetime.now()
        
        # Update in MongoDB
        users_collection.update_one({'_id': user_id}, {'$set': update_data})
        
        # Get the updated user
        updated_user = users_collection.find_one({'_id': user_id})
        updated_user['_id'] = str(updated_user['_id'])
        
        if 'role' in updated_user and updated_user['role'] and isinstance(updated_user['role'], ObjectId):
            updated_user['role'] = str(updated_user['role'])
            
        return Response(updated_user)
    
    def destroy(self, request, pk=None):
        """Delete a user"""
        try:
            user_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = users_collection.find_one({'_id': user_id})
        
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete from MongoDB
        users_collection.delete_one({'_id': user_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class TeamViewSet(viewsets.ViewSet):
    """
    API endpoint for team management
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all teams"""
        teams = list(teams_collection.find())
        
        # Convert ObjectId fields to strings
        for team in teams:
            team['_id'] = str(team['_id'])
            if 'leader' in team and team['leader'] and isinstance(team['leader'], ObjectId):
                team['leader'] = str(team['leader'])
            if 'organization' in team and team['organization'] and isinstance(team['organization'], ObjectId):
                team['organization'] = str(team['organization'])
            if 'members' in team and team['members']:
                team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                                  for member in team['members']]
        
        return Response(teams)
    
    def retrieve(self, request, pk=None):
        """Get a specific team"""
        try:
            team_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = teams_collection.find_one({'_id': team_id})
        
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert ObjectId fields to strings
        team['_id'] = str(team['_id'])
        if 'leader' in team and team['leader'] and isinstance(team['leader'], ObjectId):
            team['leader'] = str(team['leader'])
        if 'organization' in team and team['organization'] and isinstance(team['organization'], ObjectId):
                team['organization'] = str(team['organization'])
        if 'members' in team and team['members']:
            team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                              for member in team['members']]
        
        return Response(team)
    
    def create(self, request):
        """Create a new team"""
        team_data = request.data
        team_data['created_at'] = datetime.datetime.now()
        
        # Convert leader ID to ObjectId
        if 'leader' in team_data and team_data['leader']:
            try:
                team_data['leader'] = ObjectId(team_data['leader'])
            except:
                return Response({"error": "Invalid leader ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert member IDs to ObjectId
        if 'members' in team_data and team_data['members']:
            try:
                team_data['members'] = [ObjectId(member) for member in team_data['members']]
            except:
                return Response({"error": "Invalid member ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Insert into MongoDB
        result = teams_collection.insert_one(team_data)
        
        # Get the created team
        created_team = teams_collection.find_one({'_id': result.inserted_id})
        
        # Convert ObjectId fields to strings for response
        created_team['_id'] = str(created_team['_id'])
        if 'leader' in created_team and created_team['leader'] and isinstance(created_team['leader'], ObjectId):
            created_team['leader'] = str(created_team['leader'])
        if 'members' in created_team and created_team['members']:
            created_team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                                        for member in created_team['members']]
        
        return Response(created_team, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update a team"""
        try:
            team_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = teams_collection.find_one({'_id': team_id})
        
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
        update_data = request.data
        update_data['updated_at'] = datetime.datetime.now()
        
        # Convert leader ID to ObjectId
        if 'leader' in update_data and update_data['leader']:
            try:
                update_data['leader'] = ObjectId(update_data['leader'])
            except:
                return Response({"error": "Invalid leader ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert organization ID to ObjectId
        if 'organization' in update_data and update_data['organization']:
            try:
                update_data['organization'] = ObjectId(update_data['organization'])
            except:
                return Response({"error": "Invalid organization ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Convert member IDs to ObjectId
        if 'members' in update_data and update_data['members']:
            try:
                update_data['members'] = [ObjectId(member) for member in update_data['members']]
            except:
                return Response({"error": "Invalid member ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update in MongoDB
        teams_collection.update_one({'_id': team_id}, {'$set': update_data})
        
        # Get the updated team
        updated_team = teams_collection.find_one({'_id': team_id})
        
        # Convert ObjectId fields to strings for response
        updated_team['_id'] = str(updated_team['_id'])
        if 'leader' in updated_team and updated_team['leader'] and isinstance(updated_team['leader'], ObjectId):
            updated_team['leader'] = str(updated_team['leader'])
        if 'members' in updated_team and updated_team['members']:
            updated_team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                                        for member in updated_team['members']]
        
        return Response(updated_team)
    
    def destroy(self, request, pk=None):
        """Delete a team"""
        try:
            team_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = teams_collection.find_one({'_id': team_id})
        
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete from MongoDB
        teams_collection.delete_one({'_id': team_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to a team"""
        try:
            team_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = teams_collection.find_one({'_id': team_id})
        
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = ObjectId(user_id)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        user = users_collection.find_one({'_id': user_id})
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Add user to team members
        result = teams_collection.update_one(
            {'_id': team_id},
            {'$addToSet': {'members': user_id}}
        )
        
        if result.modified_count > 0:
            # Get the updated team
            updated_team = teams_collection.find_one({'_id': team_id})
            
            # Convert ObjectId fields to strings for response
            updated_team['_id'] = str(updated_team['_id'])
            if 'leader' in updated_team and updated_team['leader'] and isinstance(updated_team['leader'], ObjectId):
                updated_team['leader'] = str(updated_team['leader'])
            if 'members' in updated_team and updated_team['members']:
                updated_team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                                          for member in updated_team['members']]
            
            return Response(updated_team)
        else:
            return Response({"message": "User is already a member of this team"})
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from a team"""
        try:
            team_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        team = teams_collection.find_one({'_id': team_id})
        
        if not team:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = ObjectId(user_id)
        except:
            return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove user from team members
        result = teams_collection.update_one(
            {'_id': team_id},
            {'$pull': {'members': user_id}}
        )
        
        if result.modified_count > 0:
            # Get the updated team
            updated_team = teams_collection.find_one({'_id': team_id})
            
            # Convert ObjectId fields to strings for response
            updated_team['_id'] = str(updated_team['_id'])
            if 'leader' in updated_team and updated_team['leader'] and isinstance(updated_team['leader'], ObjectId):
                updated_team['leader'] = str(updated_team['leader'])
            if 'members' in updated_team and updated_team['members']:
                updated_team['members'] = [str(member) if isinstance(member, ObjectId) else member 
                                          for member in updated_team['members']]
            
            return Response(updated_team)
        else:
            return Response({"message": "User is not a member of this team"})

class RoleViewSet(viewsets.ViewSet):
    """
    API endpoint for role management
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all roles"""
        roles = list(roles_collection.find())
        
        # Convert ObjectId to string for serialization
        for role in roles:
            role['_id'] = str(role['_id'])
        
        return Response(roles)
    
    def retrieve(self, request, pk=None):
        """Get a specific role"""
        try:
            role_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid role ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        role = roles_collection.find_one({'_id': role_id})
        
        if not role:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert ObjectId to string for serialization
        role['_id'] = str(role['_id'])
        
        return Response(role)
    
    def create(self, request):
        """Create a new role"""
        role_data = request.data
        
        # Insert into MongoDB
        result = roles_collection.insert_one(role_data)
        
        # Get the created role
        created_role = roles_collection.find_one({'_id': result.inserted_id})
        created_role['_id'] = str(created_role['_id'])
        
        return Response(created_role, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update a role"""
        try:
            role_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid role ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        role = roles_collection.find_one({'_id': role_id})
        
        if not role:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        
        update_data = request.data
        
        # Update in MongoDB
        roles_collection.update_one({'_id': role_id}, {'$set': update_data})
        
        # Get the updated role
        updated_role = roles_collection.find_one({'_id': role_id})
        updated_role['_id'] = str(updated_role['_id'])
        
        return Response(updated_role)
    
    def destroy(self, request, pk=None):
        """Delete a role"""
        try:
            role_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid role ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        role = roles_collection.find_one({'_id': role_id})
        
        if not role:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if role is assigned to any users
        users_with_role = users_collection.count_documents({'role': role_id})
        
        if users_with_role > 0:
            return Response(
                {"error": f"Cannot delete role as it is assigned to {users_with_role} users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete from MongoDB
        roles_collection.delete_one({'_id': role_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class TeamAssignmentView(APIView):
    """
    API endpoint for assigning users to teams
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
    
    def post(self, request, format=None):
        team_id = request.data.get('team_id')
        user_ids = request.data.get('user_ids', [])
        
        if not team_id:
            return Response(
                {"error": "Team ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not user_ids:
            return Response(
                {"error": "At least one user ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Convert IDs to ObjectId
            team_id_obj = ObjectId(team_id)
            user_id_objs = [ObjectId(user_id) for user_id in user_ids]
            
            # Get the team
            team = teams_collection.find_one({'_id': team_id_obj})
            if not team:
                return Response(
                    {"error": "Team not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Update team members
            result = teams_collection.update_one(
                {'_id': team_id_obj},
                {'$addToSet': {'members': {'$each': user_id_objs}}}
            )
            
            # Access people collection
            people_collection = settings.MONGODB_DB['people']
            
            # Update team reference in each person record
            for user_id in user_id_objs:
                people_collection.update_one(
                    {'userId': user_id},
                    {'$addToSet': {'teams': team_id_obj}}
                )
            
            return Response({
                "message": f"Successfully added {len(user_ids)} users to the team",
                "team_id": str(team_id_obj),
                "added_users": [str(user_id) for user_id in user_id_objs]
            })
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error assigning users to team: {str(e)}")
            return Response(
                {"error": f"Failed to assign users to team: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PeopleListView(APIView):
    """API endpoint for getting a list of people for dropdowns"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get people from MongoDB
            people_collection = settings.MONGODB_DB['people']
            people = list(people_collection.find())
            
            # Format for frontend
            formatted_people = []
            for person in people:
                formatted_people.append({
                    'id': str(person.get('_id')),
                    'name': person.get('name', ''),
                    'email': person.get('email', ''),
                    'role': person.get('role', '')
                })
                
            return Response(formatted_people)
        except Exception as e:
            return Response(
                {"error": f"Error fetching people: {str(e)}"},
                status=500
            )