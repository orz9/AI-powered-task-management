from rest_framework import serializers

class TaskCategorySerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    color_code = serializers.CharField(required=False, default="#FF5733")

class SecurityLevelSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    required_permission_level = serializers.IntegerField(default=1)

class UserDetailsSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    role = serializers.CharField(required=False)

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(default='todo')
    priority = serializers.CharField(default='medium')
    assignedTo = serializers.CharField(required=False, allow_null=True)  # Changed from assigned_to
    assignedBy = serializers.CharField(read_only=True)  # Changed from assigned_by
    team = serializers.CharField(required=False, allow_null=True)
    dueDate = serializers.DateTimeField(required=False, allow_null=True)  # Changed from due_date
    aiGenerated = serializers.BooleanField(default=False)  # Changed from ai_generated
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    category = serializers.CharField(required=False, allow_null=True)
    security_level = serializers.CharField(required=False, allow_null=True)
    ai_confidence_score = serializers.FloatField(required=False, allow_null=True)
    
    # Nested fields
    assigned_to_details = UserDetailsSerializer(read_only=True)
    assigned_by_details = UserDetailsSerializer(read_only=True)
    category_details = TaskCategorySerializer(read_only=True)
    security_level_details = SecurityLevelSerializer(read_only=True)
    team_details = UserDetailsSerializer(read_only=True)
    
    related_tasks = serializers.ListField(child=serializers.CharField(), required=False)
    blocking_tasks = serializers.ListField(child=serializers.CharField(), required=False)

class CommentSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    task_id = serializers.CharField()
    author = serializers.CharField(read_only=True)
    content = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    author_details = UserDetailsSerializer(read_only=True)

class AttachmentSerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    task_id = serializers.CharField()
    file_path = serializers.CharField(required=False)
    file_name = serializers.CharField(required=False)
    file_type = serializers.CharField(required=False)
    file_size = serializers.IntegerField(required=False)
    uploaded_by = serializers.CharField(read_only=True)
    uploaded_at = serializers.DateTimeField(read_only=True)
    uploaded_by_details = UserDetailsSerializer(read_only=True)

class TaskHistorySerializer(serializers.Serializer):
    id = serializers.CharField(source='_id', read_only=True)
    task_id = serializers.CharField()
    user_id = serializers.CharField(source='user', read_only=True)
    change_type = serializers.CharField()
    old_value = serializers.CharField(required=False, allow_null=True)
    new_value = serializers.CharField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(read_only=True)
    user_details = UserDetailsSerializer(read_only=True)