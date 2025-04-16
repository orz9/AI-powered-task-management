from rest_framework import serializers
from .models import Task, Comment, Attachment, TaskHistory, TaskCategory, SecurityLevel
from people.models import User, Team
from people.serializers import UserSerializer, TeamSerializer


class TaskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'description', 'color_code']


class SecurityLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLevel
        fields = ['id', 'name', 'description', 'required_permission_level']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_details = UserSerializer(source='assigned_by', read_only=True)
    category_details = TaskCategorySerializer(source='category', read_only=True)
    security_level_details = SecurityLevelSerializer(source='security_level', read_only=True)
    team_details = TeamSerializer(source='team', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'parent', 'category', 'category_details', 
            'security_level', 'security_level_details', 'priority', 'status', 
            'created_at', 'updated_at', 'due_date', 'start_date', 'estimated_hours',
            'assigned_to', 'assigned_to_details', 'assigned_by', 'assigned_by_details',
            'team', 'team_details', 'ai_generated', 'ai_confidence_score',
            'related_tasks', 'blocking_tasks'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    author_details = UserSerializer(source='author', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'author_details', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'author']


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)
    
    class Meta:
        model = Attachment
        fields = ['id', 'task', 'file', 'name', 'uploaded_by', 'uploaded_by_details', 'uploaded_at']
        read_only_fields = ['uploaded_at', 'uploaded_by']


class TaskHistorySerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = TaskHistory
        fields = ['id', 'task', 'user', 'user_details', 'change_type', 'old_value', 'new_value', 'timestamp']
        read_only_fields = ['timestamp']