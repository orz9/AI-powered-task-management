from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Task, Comment, Attachment, TaskHistory, TaskCategory, SecurityLevel
from .serializers import (
    TaskSerializer, CommentSerializer, AttachmentSerializer, TaskHistorySerializer,
    TaskCategorySerializer, SecurityLevelSerializer
)
from people.permissions import IsTaskModifier, IsAdminOrManager
from people.models import User


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task management.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority', 'status']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsTaskModifier]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter tasks based on user's permissions and query parameters.
        """
        queryset = Task.objects.all()
        user = self.request.user
        
        # Security level filtering
        if not user.is_admin() and not user.is_manager():
            if user.role:
                queryset = queryset.filter(
                    Q(security_level__required_permission_level__lte=user.role.permission_level) |
                    Q(assigned_to=user) |
                    Q(team__in=user.teams.all()) |
                    Q(team__leader=user)
                )
            else:
                queryset = queryset.filter(
                    Q(assigned_to=user) |
                    Q(team__in=user.teams.all()) |
                    Q(team__leader=user)
                )
        
        # Apply query filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
            
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category__id=category_filter)
            
        assigned_to_filter = self.request.query_params.get('assigned_to')
        if assigned_to_filter:
            queryset = queryset.filter(assigned_to__id=assigned_to_filter)
            
        team_filter = self.request.query_params.get('team')
        if team_filter:
            queryset = queryset.filter(team__id=team_filter)
            
        due_before = self.request.query_params.get('due_before')
        if due_before:
            queryset = queryset.filter(due_date__lte=due_before)
            
        due_after = self.request.query_params.get('due_after')
        if due_after:
            queryset = queryset.filter(due_date__gte=due_after)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Set assigned_by to current user when creating a task.
        """
        serializer.save(assigned_by=self.request.user)
        
        # Create task history record
        task = serializer.instance
        TaskHistory.objects.create(
            task=task,
            user=self.request.user,
            change_type='task_created',
            new_value=f"Task '{task.title}' created"
        )
    
    def perform_update(self, serializer):
        """
        Track changes when updating a task.
        """
        old_instance = self.get_object()
        old_status = old_instance.status
        old_assigned_to = old_instance.assigned_to
        
        # Update the task
        serializer.save()
        new_instance = serializer.instance
        
        # Check for status change
        if old_status != new_instance.status:
            TaskHistory.objects.create(
                task=new_instance,
                user=self.request.user,
                change_type='status_change',
                old_value=old_status,
                new_value=new_instance.status
            )
            
        # Check for assignment change
        if old_assigned_to != new_instance.assigned_to:
            TaskHistory.objects.create(
                task=new_instance,
                user=self.request.user,
                change_type='assignment_change',
                old_value=str(old_assigned_to) if old_assigned_to else "Unassigned",
                new_value=str(new_instance.assigned_to) if new_instance.assigned_to else "Unassigned"
            )
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """
        Add a comment to a task.
        """
        task = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response({"error": "Comment content is required"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        comment = Comment.objects.create(
            task=task,
            author=request.user,
            content=content
        )
        
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get task history.
        """
        task = self.get_object()
        history = task.history.all().order_by('-timestamp')
        serializer = TaskHistorySerializer(history, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task comments.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only comment author or admin/manager can modify
            permission_classes = [permissions.IsAuthenticated, 
                                 lambda user: user.is_admin() or user.is_manager() or 
                                 user == self.get_object().author]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task attachments.
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_permissions(self):
        if self.action in ['destroy']:
            # Only uploader or admin/manager can delete
            permission_classes = [permissions.IsAuthenticated, 
                                 lambda user: user.is_admin() or user.is_manager() or 
                                 user == self.get_object().uploaded_by]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        task_id = self.request.data.get('task')
        task = get_object_or_404(Task, pk=task_id)
        
        serializer.save(
            uploaded_by=self.request.user,
            task=task
        )


class TaskCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task categories.
    """
    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class SecurityLevelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for security levels.
    """
    queryset = SecurityLevel.objects.all()
    serializer_class = SecurityLevelSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]