from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
import uuid


class TaskCategory(models.Model):
    """
    Categories for tasks (e.g., Development, Design, Marketing).
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default="#FF5733")  # Hex color code
    
    def __str__(self):
        return self.name


class SecurityLevel(models.Model):
    """
    Security levels for tasks to control who can view/modify them.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    required_permission_level = models.IntegerField(default=1)
    
    def __str__(self):
        return self.name


class Task(MPTTModel):
    """
    Task model using MPTT for hierarchical task relationships.
    This allows for subtasks and parent-child task relationships.
    """
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                           related_name='children')
    
    # Task metadata
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True)
    security_level = models.ForeignKey(SecurityLevel, on_delete=models.SET_NULL, null=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    
    # Dates and timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Assignments
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='created_tasks')
    team = models.ForeignKey('people.Team', on_delete=models.SET_NULL, null=True, blank=True, 
                           related_name='team_tasks')
    
    # AI-related fields
    ai_generated = models.BooleanField(default=False)
    ai_confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Task relationships
    related_tasks = models.ManyToManyField('self', blank=True, symmetrical=True)
    blocking_tasks = models.ManyToManyField('self', blank=True, symmetrical=False, 
                                          related_name='blocked_by_tasks')
    
    class MPTTMeta:
        order_insertion_by = ['priority']
    
    def __str__(self):
        return self.title
    
    def can_user_modify(self, user):
        """
        Check if a user can modify this task based on security level.
        """
        if not user.is_authenticated:
            return False
        
        # Admin/manager override
        if user.is_admin() or user.is_manager():
            return True
            
        # Check if user has required permission level
        if self.security_level and user.role:
            return user.role.permission_level >= self.security_level.required_permission_level
            
        # Task assignee can modify
        if self.assigned_to == user:
            return True
            
        # Team leader can modify team tasks
        if self.team and self.team.leader == user:
            return True
            
        return False


class Comment(models.Model):
    """
    Comments on tasks for discussion and updates.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author} on {self.task}"


class Attachment(models.Model):
    """
    File attachments for tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class TaskHistory(models.Model):
    """
    Track changes to tasks for auditing and historical reference.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    change_type = models.CharField(max_length=50)  # e.g., 'status_change', 'assignment_change'
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.change_type} by {self.user} on {self.task}"


class TranscriptionRecord(models.Model):
    """
    Store Whisper AI transcription records and metadata.
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='transcriptions/audio/', null=True, blank=True)
    transcript_text = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    tasks_created = models.ManyToManyField(Task, blank=True, related_name='source_transcriptions')
    
    def __str__(self):
        return f"Transcription by {self.created_by} on {self.created_at}"


class AITaskPrediction(models.Model):
    """
    Store AI predictions for upcoming tasks.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='task_predictions')
    prediction_text = models.TextField()
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    was_accurate = models.BooleanField(null=True, blank=True)  # For feedback/training
    converted_to_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='source_prediction')
    
    def __str__(self):
        return f"Prediction for {self.user}: {self.prediction_text[:50]}..."