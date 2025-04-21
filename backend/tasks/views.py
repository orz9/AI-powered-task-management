from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from bson import ObjectId
import datetime
import json

from .serializers import (
    TaskSerializer, CommentSerializer, AttachmentSerializer, TaskHistorySerializer,
    TaskCategorySerializer, SecurityLevelSerializer
)
from people.permissions import IsTaskModifier, IsAdminOrManager

# Get MongoDB collections
from .models import (
    tasks_collection, comments_collection, attachments_collection, 
    task_history_collection, categories_collection, security_levels_collection
)
users_collection = settings.MONGODB_DB['users']
people_collection = settings.MONGODB_DB['people']
teams_collection = settings.MONGODB_DB['teams']

class TaskViewSet(viewsets.ViewSet):
    """
    API endpoint for task management.
    """
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsTaskModifier]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all tasks"""
        # Get query parameters
        status_filter = request.query_params.get('status')
        priority_filter = request.query_params.get('priority')
        category_filter = request.query_params.get('category')
        assigned_to_filter = request.query_params.get('assigned_to')
        team_filter = request.query_params.get('team')
        due_before = request.query_params.get('due_before')
        due_after = request.query_params.get('due_after')
        
        # Build query
        query = {}
        
        if status_filter:
            query['status'] = status_filter
            
        if priority_filter:
            query['priority'] = priority_filter
            
        if category_filter:
            try:
                query['category'] = ObjectId(category_filter)
            except:
                return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        if assigned_to_filter:
            try:
                query['assigned_to'] = ObjectId(assigned_to_filter)
            except:
                return Response({"error": "Invalid assigned_to ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        if team_filter:
            try:
                query['team'] = ObjectId(team_filter)
            except:
                return Response({"error": "Invalid team ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        if due_before:
            try:
                query['due_date'] = {'$lte': datetime.datetime.fromisoformat(due_before)}
            except:
                return Response({"error": "Invalid due_before date"}, status=status.HTTP_400_BAD_REQUEST)
            
        if due_after:
            try:
                if 'due_date' not in query:
                    query['due_date'] = {}
                query['due_date']['$gte'] = datetime.datetime.fromisoformat(due_after)
            except:
                return Response({"error": "Invalid due_after date"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Security level filtering for regular users
        user = request.user
        if not hasattr(user, 'is_admin') or not user.is_admin():
            if hasattr(user, 'role') and user.role:
                security_query = [
                    {'security_level': {'$exists': False}},
                    {'security_level': None}
                ]
                
                # Get user's permission level
                user_role = roles_collection.find_one({'_id': ObjectId(user.role)})
                if user_role and 'permission_level' in user_role:
                    # Find all security levels with required_permission_level less than or equal to user's level
                    security_levels = list(security_levels_collection.find(
                        {'required_permission_level': {'$lte': user_role['permission_level']}}
                    ))
                    if security_levels:
                        security_level_ids = [level['_id'] for level in security_levels]
                        security_query.append({'security_level': {'$in': security_level_ids}})
                
                # Tasks assigned to user
                security_query.append({'assigned_to': ObjectId(str(user.id))})
                
                # Tasks for user's teams
                user_teams = list(teams_collection.find({'members': ObjectId(str(user.id))}))
                if user_teams:
                    team_ids = [team['_id'] for team in user_teams]
                    security_query.append({'team': {'$in': team_ids}})
                
                # Tasks for teams where user is leader
                led_teams = list(teams_collection.find({'leader': ObjectId(str(user.id))}))
                if led_teams:
                    led_team_ids = [team['_id'] for team in led_teams]
                    security_query.append({'team': {'$in': led_team_ids}})
                
                # Add security query to main query
                query['$or'] = security_query
        
        # Get tasks from MongoDB
        tasks = list(tasks_collection.find(query).sort('created_at', -1))
        
        # Process tasks for serialization
        for task in tasks:
            task['_id'] = str(task['_id'])
            
            if 'assigned_to' in task and task['assigned_to'] and isinstance(task['assigned_to'], ObjectId):
                task['assigned_to'] = str(task['assigned_to'])
                
                # Get assignee details
                assignee = people_collection.find_one({'_id': ObjectId(task['assigned_to'])})
                if assignee:
                    task['assigned_to_details'] = {
                        'id': str(assignee['_id']),
                        'name': assignee.get('name', ''),
                        'role': assignee.get('role', '')
                    }
            
            if 'assigned_by' in task and task['assigned_by'] and isinstance(task['assigned_by'], ObjectId):
                task['assigned_by'] = str(task['assigned_by'])
            
            if 'category' in task and task['category'] and isinstance(task['category'], ObjectId):
                task['category'] = str(task['category'])
            
            if 'security_level' in task and task['security_level'] and isinstance(task['security_level'], ObjectId):
                task['security_level'] = str(task['security_level'])
            
            if 'team' in task and task['team'] and isinstance(task['team'], ObjectId):
                task['team'] = str(task['team'])
            
            if 'related_tasks' in task and task['related_tasks']:
                task['related_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in task['related_tasks']]
            
            if 'blocking_tasks' in task and task['blocking_tasks']:
                task['blocking_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in task['blocking_tasks']]
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific task"""
        task = tasks_collection.find_one({'_id': pk})
        
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process task for serialization
        task['_id'] = str(task['_id'])
        
        if 'assigned_to' in task and task['assigned_to'] and isinstance(task['assigned_to'], ObjectId):
            task['assigned_to'] = str(task['assigned_to'])
            
            # Get assignee details
            assignee = people_collection.find_one({'_id': ObjectId(task['assigned_to'])})
            if assignee:
                task['assigned_to_details'] = {
                    'id': str(assignee['_id']),
                    'name': assignee.get('name', ''),
                    'role': assignee.get('role', '')
                }
        
        if 'assigned_by' in task and task['assigned_by'] and isinstance(task['assigned_by'], ObjectId):
            task['assigned_by'] = str(task['assigned_by'])
        
        if 'category' in task and task['category'] and isinstance(task['category'], ObjectId):
            task['category'] = str(task['category'])
            
            # Get category details
            category = categories_collection.find_one({'_id': ObjectId(task['category'])})
            if category:
                task['category_details'] = {
                    'id': str(category['_id']),
                    'name': category.get('name', ''),
                    'color_code': category.get('color_code', '#FF5733')
                }
        
        if 'security_level' in task and task['security_level'] and isinstance(task['security_level'], ObjectId):
            task['security_level'] = str(task['security_level'])
            
            # Get security level details
            security_level = security_levels_collection.find_one({'_id': ObjectId(task['security_level'])})
            if security_level:
                task['security_level_details'] = {
                    'id': str(security_level['_id']),
                    'name': security_level.get('name', ''),
                    'required_permission_level': security_level.get('required_permission_level', 1)
                }
        
        if 'team' in task and task['team'] and isinstance(task['team'], ObjectId):
            task['team'] = str(task['team'])
            
            # Get team details
            team = teams_collection.find_one({'_id': ObjectId(task['team'])})
            if team:
                task['team_details'] = {
                    'id': str(team['_id']),
                    'name': team.get('name', '')
                }
        
        if 'related_tasks' in task and task['related_tasks']:
            task['related_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in task['related_tasks']]
        
        if 'blocking_tasks' in task and task['blocking_tasks']:
            task['blocking_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in task['blocking_tasks']]
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new task"""
        serializer = TaskSerializer(data=request.data)
        
        if serializer.is_valid():
            task_data = serializer.validated_data
            
            # Add created_at and updated_at timestamps
            task_data['created_at'] = datetime.datetime.now()
            task_data['updated_at'] = datetime.datetime.now()
            
            # Set assigned_by to current user
            task_data['assigned_by'] = ObjectId(str(request.user.id))
            
            # Convert string IDs to ObjectId
            if 'assigned_to' in task_data and task_data['assigned_to']:
                task_data['assigned_to'] = ObjectId(task_data['assigned_to'])
            
            if 'category' in task_data and task_data['category']:
                task_data['category'] = ObjectId(task_data['category'])
            
            if 'security_level' in task_data and task_data['security_level']:
                task_data['security_level'] = ObjectId(task_data['security_level'])
            
            if 'team' in task_data and task_data['team']:
                task_data['team'] = ObjectId(task_data['team'])
            
            # Insert task into MongoDB
            result = tasks_collection.insert_one(task_data)
            task_id = result.inserted_id
            
            # Create task history record
            history_data = {
                'task_id': task_id,
                'user_id': ObjectId(str(request.user.id)),
                'change_type': 'task_created',
                'new_value': f"Task '{task_data.get('title', '')}' created",
                'timestamp': datetime.datetime.now()
            }
            task_history_collection.insert_one(history_data)
            
            # Get the created task
            created_task = tasks_collection.find_one({'_id': task_id})
            
            # Process task for serialization
            created_task['_id'] = str(created_task['_id'])
            
            if 'assigned_to' in created_task and created_task['assigned_to'] and isinstance(created_task['assigned_to'], ObjectId):
                created_task['assigned_to'] = str(created_task['assigned_to'])
            
            if 'assigned_by' in created_task and created_task['assigned_by'] and isinstance(created_task['assigned_by'], ObjectId):
                created_task['assigned_by'] = str(created_task['assigned_by'])
            
            if 'category' in created_task and created_task['category'] and isinstance(created_task['category'], ObjectId):
                created_task['category'] = str(created_task['category'])
            
            if 'security_level' in created_task and created_task['security_level'] and isinstance(created_task['security_level'], ObjectId):
                created_task['security_level'] = str(created_task['security_level'])
            
            if 'team' in created_task and created_task['team'] and isinstance(created_task['team'], ObjectId):
                created_task['team'] = str(created_task['team'])
            
            return Response(created_task, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update a task"""
        try:
            task_id = pk
        except:
            return Response({"error": "Invalid task ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = tasks_collection.find_one({'_id': task_id})
        
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            update_data = serializer.validated_data
            
            # Track old values for history
            old_status = task.get('status')
            old_assigned_to = task.get('assigned_to')
            
            # Update timestamp
            update_data['updated_at'] = datetime.datetime.now()
            
            # Convert string IDs to ObjectId
            if 'assigned_to' in update_data and update_data['assigned_to']:
                update_data['assigned_to'] = ObjectId(update_data['assigned_to'])
            
            if 'category' in update_data and update_data['category']:
                update_data['category'] = ObjectId(update_data['category'])
            
            if 'security_level' in update_data and update_data['security_level']:
                update_data['security_level'] = ObjectId(update_data['security_level'])
            
            if 'team' in update_data and update_data['team']:
                update_data['team'] = ObjectId(update_data['team'])
            
            # Update task in MongoDB
            tasks_collection.update_one({'_id': task_id}, {'$set': update_data})
            
            # Create history records for important changes
            # Check for status change
            if 'status' in update_data and old_status != update_data['status']:
                history_data = {
                    'task_id': task_id,
                    'user_id': ObjectId(str(request.user.id)),
                    'change_type': 'status_change',
                    'old_value': old_status,
                    'new_value': update_data['status'],
                    'timestamp': datetime.datetime.now()
                }
                task_history_collection.insert_one(history_data)
            
            # Check for assignment change
            if 'assigned_to' in update_data and old_assigned_to != update_data['assigned_to']:
                history_data = {
                    'task_id': task_id,
                    'user_id': ObjectId(str(request.user.id)),
                    'change_type': 'assignment_change',
                    'old_value': str(old_assigned_to) if old_assigned_to else "Unassigned",
                    'new_value': str(update_data['assigned_to']) if update_data['assigned_to'] else "Unassigned",
                    'timestamp': datetime.datetime.now()
                }
                task_history_collection.insert_one(history_data)
            
            # Get the updated task
            updated_task = tasks_collection.find_one({'_id': task_id})
            
            # Process task for serialization
            updated_task['_id'] = str(updated_task['_id'])
            
            if 'assigned_to' in updated_task and updated_task['assigned_to'] and isinstance(updated_task['assigned_to'], ObjectId):
                updated_task['assigned_to'] = str(updated_task['assigned_to'])
            
            if 'assigned_by' in updated_task and updated_task['assigned_by'] and isinstance(updated_task['assigned_by'], ObjectId):
                updated_task['assigned_by'] = str(updated_task['assigned_by'])
            
            if 'category' in updated_task and updated_task['category'] and isinstance(updated_task['category'], ObjectId):
                updated_task['category'] = str(updated_task['category'])
            
            if 'security_level' in updated_task and updated_task['security_level'] and isinstance(updated_task['security_level'], ObjectId):
                updated_task['security_level'] = str(updated_task['security_level'])
            
            if 'team' in updated_task and updated_task['team'] and isinstance(updated_task['team'], ObjectId):
                updated_task['team'] = str(updated_task['team'])
            
            if 'related_tasks' in updated_task and updated_task['related_tasks']:
                updated_task['related_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in updated_task['related_tasks']]
            
            if 'blocking_tasks' in updated_task and updated_task['blocking_tasks']:
                updated_task['blocking_tasks'] = [str(t) if isinstance(t, ObjectId) else t for t in updated_task['blocking_tasks']]
            
            return Response(updated_task)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a task"""
        try:
            task_id = pk
        except:
            return Response({"error": "Invalid task ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = tasks_collection.find_one({'_id': task_id})
        
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete task from MongoDB
        tasks_collection.delete_one({'_id': task_id})
        
        # Delete related comments and attachments
        comments_collection.delete_many({'task_id': task_id})
        attachments_collection.delete_many({'task_id': task_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a task"""
        try:
            task_id = pk
        except:
            return Response({"error": "Invalid task ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = tasks_collection.find_one({'_id': task_id})
        
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        content = request.data.get('content')
        if not content:
            return Response({"error": "Comment content is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create comment
        comment_data = {
            'task_id': task_id,
            'author': ObjectId(str(request.user.id)),
            'content': content,
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }
        
        result = comments_collection.insert_one(comment_data)
        
        # Get created comment
        comment = comments_collection.find_one({'_id': result.inserted_id})
        
        # Process for serialization
        comment['_id'] = str(comment['_id'])
        if 'author' in comment and isinstance(comment['author'], ObjectId):
            comment['author'] = str(comment['author'])
            
            # Get author details
            author = users_collection.find_one({'_id': ObjectId(comment['author'])})
            if author:
                comment['author_details'] = {
                    'id': str(author['_id']),
                    'username': author.get('username', ''),
                    'first_name': author.get('first_name', ''),
                    'last_name': author.get('last_name', '')
                }
        
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get task history"""
        try:
            task_id = pk
        except:
            return Response({"error": "Invalid task ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        task = tasks_collection.find_one({'_id': task_id})
        
        if not task:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get history records
        history = list(task_history_collection.find({'task_id': task_id}).sort('timestamp', -1))
        
        # Process for serialization
        for record in history:
            record['_id'] = str(record['_id'])
            
            if 'user_id' in record and isinstance(record['user_id'], ObjectId):
                record['user'] = str(record['user_id'])
                
                # Get user details
                user = users_collection.find_one({'_id': record['user_id']})
                if user:
                    record['user_details'] = {
                        'id': str(user['_id']),
                        'username': user.get('username', ''),
                        'first_name': user.get('first_name', ''),
                        'last_name': user.get('last_name', '')
                    }
        
        serializer = TaskHistorySerializer(history, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ViewSet):
    """
    API endpoint for task comments.
    """
    
    def get_permissions(self):
        # Only comment author or admin/manager can modify
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]  # Custom permission check in methods
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List comments (with optional task filter)"""
        task_id = request.query_params.get('task')
        
        if task_id:
            comments = list(comments_collection.find({'task_id': task_id}).sort('created_at', 1))
        else:
            comments = list(comments_collection.find().sort('created_at', -1).limit(50))
        
        # Process for serialization
        for comment in comments:
            comment['_id'] = str(comment['_id'])
            
            if 'author' in comment and isinstance(comment['author'], ObjectId):
                comment['author'] = str(comment['author'])
                
                # Get author details
                author = users_collection.find_one({'_id': ObjectId(comment['author'])})
                if author:
                    comment['author_details'] = {
                        'id': str(author['_id']),
                        'username': author.get('username', ''),
                        'first_name': author.get('first_name', ''),
                        'last_name': author.get('last_name', '')
                    }
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific comment"""
        try:
            comment_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid comment ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        comment = comments_collection.find_one({'_id': comment_id})
        
        if not comment:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process for serialization
        comment['_id'] = str(comment['_id'])
        
        if 'author' in comment and isinstance(comment['author'], ObjectId):
            comment['author'] = str(comment['author'])
            
            # Get author details
            author = users_collection.find_one({'_id': ObjectId(comment['author'])})
            if author:
                comment['author_details'] = {
                    'id': str(author['_id']),
                    'username': author.get('username', ''),
                    'first_name': author.get('first_name', ''),
                    'last_name': author.get('last_name', '')
                }
        
        serializer = CommentSerializer(comment)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new comment"""
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            comment_data = serializer.validated_data
            
            # Set author to current user
            comment_data['author'] = ObjectId(str(request.user.id))
            
            # Add timestamps
            comment_data['created_at'] = datetime.datetime.now()
            comment_data['updated_at'] = datetime.datetime.now()
            
            # Insert into MongoDB
            result = comments_collection.insert_one(comment_data)
            
            # Get the created comment
            comment = comments_collection.find_one({'_id': result.inserted_id})
            
            # Process for serialization
            comment['_id'] = str(comment['_id'])
            
            if 'author' in comment and isinstance(comment['author'], ObjectId):
                comment['author'] = str(comment['author'])
                
                # Get author details
                author = users_collection.find_one({'_id': ObjectId(comment['author'])})
                if author:
                    comment['author_details'] = {
                        'id': str(author['_id']),
                        'username': author.get('username', ''),
                        'first_name': author.get('first_name', ''),
                        'last_name': author.get('last_name', '')
                    }
            
            return Response(comment, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update a comment"""
        try:
            comment_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid comment ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        comment = comments_collection.find_one({'_id': comment_id})
        
        if not comment:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is author or admin/manager
        if str(comment.get('author')) != str(request.user.id) and not (hasattr(request.user, 'is_admin') and request.user.is_admin()) and not (hasattr(request.user, 'is_manager') and request.user.is_manager()):
            return Response({"error": "You don't have permission to update this comment"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            update_data = serializer.validated_data
            
            # Update timestamp
            update_data['updated_at'] = datetime.datetime.now()
            
            # Update in MongoDB
            comments_collection.update_one({'_id': comment_id}, {'$set': update_data})
            
            # Get updated comment
            updated_comment = comments_collection.find_one({'_id': comment_id})
            
            # Process for serialization
            updated_comment['_id'] = str(updated_comment['_id'])
            
            if 'author' in updated_comment and isinstance(updated_comment['author'], ObjectId):
                updated_comment['author'] = str(updated_comment['author'])
                
                # Get author details
                author = users_collection.find_one({'_id': ObjectId(updated_comment['author'])})
                if author:
                    updated_comment['author_details'] = {
                        'id': str(author['_id']),
                        'username': author.get('username', ''),
                        'first_name': author.get('first_name', ''),
                        'last_name': author.get('last_name', '')
                    }
            
            return Response(updated_comment)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a comment"""
        try:
            comment_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid comment ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        comment = comments_collection.find_one({'_id': comment_id})
        
        if not comment:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is author or admin/manager
        if str(comment.get('author')) != str(request.user.id) and not (hasattr(request.user, 'is_admin') and request.user.is_admin()) and not (hasattr(request.user, 'is_manager') and request.user.is_manager()):
            return Response({"error": "You don't have permission to delete this comment"}, status=status.HTTP_403_FORBIDDEN)
        
        # Delete from MongoDB
        comments_collection.delete_one({'_id': comment_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttachmentViewSet(viewsets.ViewSet):
    """
    API endpoint for task attachments.
    """
    
    def get_permissions(self):
        # Only uploader or admin/manager can delete
        if self.action in ['destroy']:
            permission_classes = [permissions.IsAuthenticated]  # Custom permission check in destroy method
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List attachments (with optional task filter)"""
        task_id = request.query_params.get('task')
        
        if task_id:
            attachments = list(attachments_collection.find({'task_id': task_id}))
        else:
            attachments = list(attachments_collection.find().limit(50))
        
        # Process for serialization
        for attachment in attachments:
            attachment['_id'] = str(attachment['_id'])
            
            if 'uploaded_by' in attachment and isinstance(attachment['uploaded_by'], ObjectId):
                attachment['uploaded_by'] = str(attachment['uploaded_by'])
                
                # Get uploader details
                uploader = users_collection.find_one({'_id': ObjectId(attachment['uploaded_by'])})
                if uploader:
                    attachment['uploaded_by_details'] = {
                        'id': str(uploader['_id']),
                        'username': uploader.get('username', ''),
                        'first_name': uploader.get('first_name', ''),
                        'last_name': uploader.get('last_name', '')
                    }
        
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific attachment"""
        try:
            attachment_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid attachment ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        attachment = attachments_collection.find_one({'_id': attachment_id})
        
        if not attachment:
            return Response({"error": "Attachment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process for serialization
        attachment['_id'] = str(attachment['_id'])
        
        if 'uploaded_by' in attachment and isinstance(attachment['uploaded_by'], ObjectId):
            attachment['uploaded_by'] = str(attachment['uploaded_by'])
            
            # Get uploader details
            uploader = users_collection.find_one({'_id': ObjectId(attachment['uploaded_by'])})
            if uploader:
                attachment['uploaded_by_details'] = {
                    'id': str(uploader['_id']),
                    'username': uploader.get('username', ''),
                    'first_name': uploader.get('first_name', ''),
                    'last_name': uploader.get('last_name', '')
                }
        
        serializer = AttachmentSerializer(attachment)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new attachment"""
        # For file uploads with Django REST framework
        serializer = AttachmentSerializer(data=request.data)
        
        if serializer.is_valid():
            attachment_data = serializer.validated_data
            
            # Set uploaded_by to current user
            attachment_data['uploaded_by'] = ObjectId(str(request.user.id))
            
            # Add uploaded_at timestamp
            attachment_data['uploaded_at'] = datetime.datetime.now()
            
            # Handle file upload (this depends on your file storage method)
            if 'file' in request.FILES:
                file_obj = request.FILES['file']
                # Store file reference or path in attachment_data
                # This implementation depends on your file storage method
                # For example, if using Django's default storage:
                from django.core.files.storage import default_storage
                path = default_storage.save(f"attachments/{file_obj.name}", file_obj)
                attachment_data['file_path'] = path
                attachment_data['file_name'] = file_obj.name
                attachment_data['file_type'] = file_obj.content_type
                attachment_data['file_size'] = file_obj.size
            
            # Insert into MongoDB
            result = attachments_collection.insert_one(attachment_data)
            
            # Get the created attachment
            attachment = attachments_collection.find_one({'_id': result.inserted_id})
            
            # Process for serialization
            attachment['_id'] = str(attachment['_id'])
            
            if 'uploaded_by' in attachment and isinstance(attachment['uploaded_by'], ObjectId):
                attachment['uploaded_by'] = str(attachment['uploaded_by'])
            
            return Response(attachment, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete an attachment"""
        try:
            attachment_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid attachment ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        attachment = attachments_collection.find_one({'_id': attachment_id})
        
        if not attachment:
            return Response({"error": "Attachment not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is uploader or admin/manager
        if str(attachment.get('uploaded_by')) != str(request.user.id) and not (hasattr(request.user, 'is_admin') and request.user.is_admin()) and not (hasattr(request.user, 'is_manager') and request.user.is_manager()):
            return Response({"error": "You don't have permission to delete this attachment"}, status=status.HTTP_403_FORBIDDEN)
        
        # Delete file from storage (implementation depends on your storage method)
        if 'file_path' in attachment:
            try:
                from django.core.files.storage import default_storage
                default_storage.delete(attachment['file_path'])
            except Exception as e:
                # Log error but continue with attachment deletion
                print(f"Error deleting file: {str(e)}")
        
        # Delete from MongoDB
        attachments_collection.delete_one({'_id': attachment_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCategoryViewSet(viewsets.ViewSet):
    """
    API endpoint for task categories.
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all categories"""
        categories = list(categories_collection.find())
        
        # Process for serialization
        for category in categories:
            category['_id'] = str(category['_id'])
        
        serializer = TaskCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific category"""
        try:
            category_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        category = categories_collection.find_one({'_id': category_id})
        
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process for serialization
        category['_id'] = str(category['_id'])
        
        serializer = TaskCategorySerializer(category)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new category"""
        serializer = TaskCategorySerializer(data=request.data)
        
        if serializer.is_valid():
            category_data = serializer.validated_data
            
            # Set default color if not provided
            if 'color_code' not in category_data:
                category_data['color_code'] = "#FF5733"  # Default color
            
            # Insert into MongoDB
            result = categories_collection.insert_one(category_data)
            
            # Get the created category
            category = categories_collection.find_one({'_id': result.inserted_id})
            category['_id'] = str(category['_id'])
            
            return Response(category, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update a category"""
        try:
            category_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        category = categories_collection.find_one({'_id': category_id})
        
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskCategorySerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            update_data = serializer.validated_data
            
            # Update in MongoDB
            categories_collection.update_one({'_id': category_id}, {'$set': update_data})
            
            # Get the updated category
            updated_category = categories_collection.find_one({'_id': category_id})
            updated_category['_id'] = str(updated_category['_id'])
            
            return Response(updated_category)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a category"""
        try:
            category_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        category = categories_collection.find_one({'_id': category_id})
        
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if category is used by any tasks
        tasks_with_category = tasks_collection.count_documents({'category': category_id})
        
        if tasks_with_category > 0:
            return Response(
                {"error": f"Cannot delete category as it is used by {tasks_with_category} tasks"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete from MongoDB
        categories_collection.delete_one({'_id': category_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class SecurityLevelViewSet(viewsets.ViewSet):
    """
    API endpoint for security levels.
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def list(self, request):
        """List all security levels"""
        security_levels = list(security_levels_collection.find())
        
        # Process for serialization
        for level in security_levels:
            level['_id'] = str(level['_id'])
        
        serializer = SecurityLevelSerializer(security_levels, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get a specific security level"""
        try:
            level_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid security level ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        level = security_levels_collection.find_one({'_id': level_id})
        
        if not level:
            return Response({"error": "Security level not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process for serialization
        level['_id'] = str(level['_id'])
        
        serializer = SecurityLevelSerializer(level)
        return Response(serializer.data)
    
    def create(self, request):
        """Create a new task"""
        print("Received task data:", request.data)  # Log the received data
        serializer = TaskSerializer(data=request.data)

        if serializer.is_valid():
            level_data = serializer.validated_data
            
            # Set default permission level if not provided
            if 'required_permission_level' not in level_data:
                level_data['required_permission_level'] = 1  # Default permission level
            
            # Insert into MongoDB
            result = security_levels_collection.insert_one(level_data)
            
            # Get the created security level
            level = security_levels_collection.find_one({'_id': result.inserted_id})
            level['_id'] = str(level['_id'])
            
            return Response(level, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors:", serializer.errors)  # Log validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk=None):
        """Update a security level"""
        try:
            level_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid security level ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        level = security_levels_collection.find_one({'_id': level_id})
        
        if not level:
            return Response({"error": "Security level not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SecurityLevelSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            update_data = serializer.validated_data
            
            # Update in MongoDB
            security_levels_collection.update_one({'_id': level_id}, {'$set': update_data})
            
            # Get the updated security level
            updated_level = security_levels_collection.find_one({'_id': level_id})
            updated_level['_id'] = str(updated_level['_id'])
            
            return Response(updated_level)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a security level"""
        try:
            level_id = ObjectId(pk)
        except:
            return Response({"error": "Invalid security level ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        level = security_levels_collection.find_one({'_id': level_id})
        
        if not level:
            return Response({"error": "Security level not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if security level is used by any tasks
        tasks_with_level = tasks_collection.count_documents({'security_level': level_id})
        
        if tasks_with_level > 0:
            return Response(
                {"error": f"Cannot delete security level as it is used by {tasks_with_level} tasks"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete from MongoDB
        security_levels_collection.delete_one({'_id': level_id})
        
        return Response(status=status.HTTP_204_NO_CONTENT)