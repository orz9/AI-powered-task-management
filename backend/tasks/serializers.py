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
    title = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(default='todo')
    priority = serializers.CharField(default='medium')
    
    # Frontend fields in camelCase
    assignedTo = serializers.CharField(source='assigned_to', required=False, allow_null=True, allow_blank=True)
    assignedBy = serializers.CharField(source='assigned_by', read_only=True)
    dueDate = serializers.DateTimeField(source='due_date', required=False, allow_null=True)
    aiGenerated = serializers.BooleanField(source='ai_generated', default=False, required=False)
    
    # Backend fields
    team = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    category = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    security_level = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ai_confidence_score = serializers.FloatField(required=False, allow_null=True)
    
    # Nested fields
    assigned_to_details = UserDetailsSerializer(read_only=True)
    assigned_by_details = UserDetailsSerializer(read_only=True)
    category_details = TaskCategorySerializer(read_only=True)
    security_level_details = SecurityLevelSerializer(read_only=True)
    team_details = UserDetailsSerializer(read_only=True)
    
    related_tasks = serializers.ListField(child=serializers.CharField(), required=False)
    blocking_tasks = serializers.ListField(child=serializers.CharField(), required=False)
    
    def to_representation(self, instance):
        """Convert the MongoDB document to a serializable format."""
        # Make sure instance is a dict
        if not isinstance(instance, dict):
            instance = dict(instance)
            
        # Convert ObjectId to string if needed
        if '_id' in instance and instance['_id']:
            instance['_id'] = str(instance['_id'])
            
        # Convert additional fields if needed
        for field in ['assigned_to', 'assigned_by', 'team', 'category', 'security_level']:
            if field in instance and instance[field]:
                instance[field] = str(instance[field])
                
        # Handle related tasks and nested fields
        if 'related_tasks' in instance and instance['related_tasks']:
            instance['related_tasks'] = [str(t) for t in instance['related_tasks']]
            
        if 'blocking_tasks' in instance and instance['blocking_tasks']:
            instance['blocking_tasks'] = [str(t) for t in instance['blocking_tasks']]
            
        # Let the parent class handle the rest
        return super().to_representation(instance)
    
    def to_internal_value(self, data):
        """Convert incoming data to the correct format for MongoDB."""
        # Handle camelCase to snake_case conversion
        if 'assignedTo' in data and not 'assigned_to' in data:
            data['assigned_to'] = data.pop('assignedTo')
            
        if 'dueDate' in data and not 'due_date' in data:
            data['due_date'] = data.pop('dueDate')
            
        if 'aiGenerated' in data and not 'ai_generated' in data:
            data['ai_generated'] = data.pop('aiGenerated')
            
        # Let the parent class handle the rest
        return super().to_internal_value(data)
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