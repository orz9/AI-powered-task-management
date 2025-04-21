# tasks/models.py
from django.conf import settings
from bson import ObjectId
import datetime
import uuid

# Access MongoDB collections
tasks_collection = settings.MONGODB_DB['tasks']
comments_collection = settings.MONGODB_DB['comments']
attachments_collection = settings.MONGODB_DB['attachments']
task_history_collection = settings.MONGODB_DB['task_history']
categories_collection = settings.MONGODB_DB['task_categories']
security_levels_collection = settings.MONGODB_DB['security_levels']
transcription_collection = settings.MONGODB_DB['transcription_records']
ai_prediction_collection = settings.MONGODB_DB['ai_task_predictions']

class TaskCategory:
    """
    Categories for tasks (e.g., Development, Design, Marketing).
    Using PyMongo directly.
    """
    
    @staticmethod
    def create(data):
        """Create a new task category"""
        if 'color_code' not in data:
            data['color_code'] = "#FF5733"  # Default color
            
        result = categories_collection.insert_one(data)
        data['_id'] = result.inserted_id
        return data
    
    @staticmethod
    def get_by_id(category_id):
        """Get a category by ID"""
        if isinstance(category_id, str):
            try:
                category_id = ObjectId(category_id)
            except:
                return None
                
        return categories_collection.find_one({'_id': category_id})
    
    @staticmethod
    def get_all():
        """Get all categories"""
        return list(categories_collection.find())
    
    @staticmethod
    def update(category_id, update_data):
        """Update a category"""
        if isinstance(category_id, str):
            try:
                category_id = ObjectId(category_id)
            except:
                return None
                
        result = categories_collection.update_one(
            {'_id': category_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return TaskCategory.get_by_id(category_id)
        return None
    
    @staticmethod
    def delete(category_id):
        """Delete a category"""
        if isinstance(category_id, str):
            try:
                category_id = ObjectId(category_id)
            except:
                return False
                
        result = categories_collection.delete_one({'_id': category_id})
        return result.deleted_count > 0


class SecurityLevel:
    """
    Security levels for tasks to control who can view/modify them.
    Using PyMongo directly.
    """
    
    @staticmethod
    def create(data):
        """Create a new security level"""
        if 'required_permission_level' not in data:
            data['required_permission_level'] = 1  # Default permission level
            
        result = security_levels_collection.insert_one(data)
        data['_id'] = result.inserted_id
        return data
    
    @staticmethod
    def get_by_id(level_id):
        """Get a security level by ID"""
        if isinstance(level_id, str):
            try:
                level_id = ObjectId(level_id)
            except:
                return None
                
        return security_levels_collection.find_one({'_id': level_id})
    
    @staticmethod
    def get_all():
        """Get all security levels"""
        return list(security_levels_collection.find())


class Task:
    """
    Task model implementation using PyMongo directly.
    Supports hierarchical relationships using a parent field.
    """
    
    PRIORITY_CHOICES = {
        1: 'Low',
        2: 'Medium',
        3: 'High',
        4: 'Critical',
    }
    
    STATUS_CHOICES = [
        'backlog', 'todo', 'in_progress', 'review', 'done', 'archived'
    ]
    
    @staticmethod
    def create(task_data):
        """Create a new task"""
        # Generate UUID for task ID
        if '_id' not in task_data:
            task_data['_id'] = str(uuid.uuid4())
            
        # Set defaults 
        if 'created_at' not in task_data:
            task_data['created_at'] = datetime.datetime.now()
            
        if 'updated_at' not in task_data:
            task_data['updated_at'] = datetime.datetime.now()
            
        if 'status' not in task_data:
            task_data['status'] = 'todo'
            
        if 'priority' not in task_data:
            task_data['priority'] = 2  # Medium
            
        if 'ai_generated' not in task_data:
            task_data['ai_generated'] = False
            
        # Insert and return
        tasks_collection.insert_one(task_data)
        return task_data
    
    @staticmethod
    def get_by_id(task_id):
        """Get a task by ID"""
        return tasks_collection.find_one({'_id': task_id})
    
    @staticmethod
    def get_all(filters=None, sort=None, limit=100, skip=0):
        """Get all tasks with optional filtering"""
        query = filters if filters else {}
        
        # Define sort order
        sort_order = sort if sort else [('created_at', -1)]  # Descending by created_at
        
        return list(tasks_collection.find(query).sort(sort_order).skip(skip).limit(limit))
    
    @staticmethod
    def update(task_id, update_data):
        """Update a task"""
        # Always update the updated_at timestamp
        update_data['updated_at'] = datetime.datetime.now()
        
        # Perform the update
        result = tasks_collection.update_one(
            {'_id': task_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return Task.get_by_id(task_id)
        return None
    
    @staticmethod
    def delete(task_id):
        """Delete a task"""
        # Delete the task
        result = tasks_collection.delete_one({'_id': task_id})
        
        # Delete all related comments and attachments
        if result.deleted_count > 0:
            comments_collection.delete_many({'task_id': task_id})
            attachments_collection.delete_many({'task_id': task_id})
            
        return result.deleted_count > 0
    
    @staticmethod
    def get_by_user(user_id, status=None):
        """Get tasks assigned to a specific user"""
        query = {'assigned_to': user_id}
        
        if status:
            query['status'] = status
            
        return list(tasks_collection.find(query).sort('created_at', -1))
    
    @staticmethod
    def get_by_team(team_id):
        """Get tasks for a specific team"""
        return list(tasks_collection.find({'team': team_id}).sort('created_at', -1))
    
    @staticmethod
    def get_children(task_id):
        """Get all child tasks for a parent task"""
        return list(tasks_collection.find({'parent': task_id}).sort('priority', 1))
    
    @staticmethod
    def add_related_task(task_id, related_task_id):
        """Add a related task (bidirectional relationship)"""
        # Add to first task
        tasks_collection.update_one(
            {'_id': task_id},
            {'$addToSet': {'related_tasks': related_task_id}}
        )
        
        # Add to the related task (symmetrical)
        tasks_collection.update_one(
            {'_id': related_task_id},
            {'$addToSet': {'related_tasks': task_id}}
        )
    
    @staticmethod
    def add_blocking_task(task_id, blocking_task_id):
        """Add a blocking task relationship"""
        # Update that this task is blocked by another
        tasks_collection.update_one(
            {'_id': task_id},
            {'$addToSet': {'blocking_tasks': blocking_task_id}}
        )
        
        # Update that the blocking task blocks this one
        tasks_collection.update_one(
            {'_id': blocking_task_id},
            {'$addToSet': {'blocked_by_tasks': task_id}}
        )
    
    @staticmethod
    def can_user_modify(task, user):
        """
        Check if a user can modify this task based on security level.
        """
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return False
        
        # Admin/manager override
        if hasattr(user, 'is_admin') and user.is_admin():
            return True
            
        if hasattr(user, 'is_manager') and user.is_manager():
            return True
            
        # Get user data if not available directly
        user_data = getattr(user, 'mongo_user', None)
        
        # Check if user has required permission level
        if 'security_level' in task and task['security_level'] and user_data and 'role' in user_data:
            # Get security level details
            security_level = SecurityLevel.get_by_id(task['security_level'])
            
            if security_level and 'required_permission_level' in security_level:
                user_permission = user_data['role'].get('permission_level', 0)
                return user_permission >= security_level['required_permission_level']
            
        # Task assignee can modify
        if 'assigned_to' in task and task['assigned_to'] == str(user.id):
            return True
            
        # Team leader can modify team tasks
        if 'team' in task and task['team']:
            from people.models import Team
            team = Team.get_by_id(task['team'])
            
            if team and 'leader' in team and team['leader'] == str(user.id):
                return True
            
        return False


class Comment:
    """
    Comments on tasks implementation using PyMongo directly.
    """
    
    @staticmethod
    def create(comment_data):
        """Create a new comment"""
        if 'created_at' not in comment_data:
            comment_data['created_at'] = datetime.datetime.now()
            
        if 'updated_at' not in comment_data:
            comment_data['updated_at'] = datetime.datetime.now()
            
        result = comments_collection.insert_one(comment_data)
        comment_data['_id'] = result.inserted_id
        return comment_data
    
    @staticmethod
    def get_by_task(task_id, sort=None):
        """Get all comments for a task"""
        sort_order = sort if sort else [('created_at', 1)]  # Ascending by created_at
        return list(comments_collection.find({'task_id': task_id}).sort(sort_order))
    
    @staticmethod
    def update(comment_id, update_data):
        """Update a comment"""
        if isinstance(comment_id, str):
            try:
                comment_id = ObjectId(comment_id)
            except:
                return None
                
        # Always update the updated_at timestamp
        update_data['updated_at'] = datetime.datetime.now()
        
        # Perform the update
        result = comments_collection.update_one(
            {'_id': comment_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return comments_collection.find_one({'_id': comment_id})
        return None
    
    @staticmethod
    def delete(comment_id):
        """Delete a comment"""
        if isinstance(comment_id, str):
            try:
                comment_id = ObjectId(comment_id)
            except:
                return False
                
        result = comments_collection.delete_one({'_id': comment_id})
        return result.deleted_count > 0


class Attachment:
    """
    File attachments for tasks implementation using PyMongo directly.
    """
    
    @staticmethod
    def create(attachment_data):
        """Create a new attachment"""
        if 'uploaded_at' not in attachment_data:
            attachment_data['uploaded_at'] = datetime.datetime.now()
            
        result = attachments_collection.insert_one(attachment_data)
        attachment_data['_id'] = result.inserted_id
        return attachment_data
    
    @staticmethod
    def get_by_task(task_id):
        """Get all attachments for a task"""
        return list(attachments_collection.find({'task_id': task_id}))
    
    @staticmethod
    def delete(attachment_id):
        """Delete an attachment"""
        if isinstance(attachment_id, str):
            try:
                attachment_id = ObjectId(attachment_id)
            except:
                return False
                
        result = attachments_collection.delete_one({'_id': attachment_id})
        return result.deleted_count > 0


class TaskHistory:
    """
    Track changes to tasks for auditing and historical reference.
    Implementation using PyMongo directly.
    """
    
    @staticmethod
    def create(history_data):
        """Create a new history record"""
        if 'timestamp' not in history_data:
            history_data['timestamp'] = datetime.datetime.now()
            
        result = task_history_collection.insert_one(history_data)
        history_data['_id'] = result.inserted_id
        return history_data
    
    @staticmethod
    def get_by_task(task_id, limit=50):
        """Get history for a task"""
        return list(
            task_history_collection.find({'task_id': task_id})
            .sort('timestamp', -1)
            .limit(limit)
        )
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get history entries created by a user"""
        return list(
            task_history_collection.find({'user_id': user_id})
            .sort('timestamp', -1)
            .limit(limit)
        )


class TranscriptionRecord:
    """
    Store Whisper AI transcription records and metadata.
    Implementation using PyMongo directly.
    """
    
    @staticmethod
    def create(transcription_data):
        """Create a new transcription record"""
        if 'created_at' not in transcription_data:
            transcription_data['created_at'] = datetime.datetime.now()
            
        result = transcription_collection.insert_one(transcription_data)
        transcription_data['_id'] = result.inserted_id
        return transcription_data
    
    @staticmethod
    def get_by_id(record_id):
        """Get a transcription record by ID"""
        if isinstance(record_id, str):
            try:
                record_id = ObjectId(record_id)
            except:
                return None
                
        return transcription_collection.find_one({'_id': record_id})
    
    @staticmethod
    def get_by_user(user_id, limit=10):
        """Get transcription records for a specific user"""
        return list(
            transcription_collection.find({'created_by': user_id})
            .sort('created_at', -1)
            .limit(limit)
        )
    
    @staticmethod
    def add_task(transcription_id, task_id):
        """Add a task created from this transcription"""
        if isinstance(transcription_id, str):
            try:
                transcription_id = ObjectId(transcription_id)
            except:
                return False
                
        result = transcription_collection.update_one(
            {'_id': transcription_id},
            {'$addToSet': {'tasks_created': task_id}}
        )
        
        return result.modified_count > 0


class AITaskPrediction:
    """
    Store AI predictions for upcoming tasks.
    Implementation using PyMongo directly.
    """
    
    @staticmethod
    def create(prediction_data):
        """Create a new AI task prediction"""
        if 'created_at' not in prediction_data:
            prediction_data['created_at'] = datetime.datetime.now()
            
        result = ai_prediction_collection.insert_one(prediction_data)
        prediction_data['_id'] = result.inserted_id
        return prediction_data
    
    @staticmethod
    def get_by_id(prediction_id):
        """Get a prediction by ID"""
        if isinstance(prediction_id, str):
            try:
                prediction_id = ObjectId(prediction_id)
            except:
                return None
                
        return ai_prediction_collection.find_one({'_id': prediction_id})
    
    @staticmethod
    def get_by_user(user_id, active_only=True):
        """Get predictions for a specific user"""
        query = {'user_id': user_id}
        
        if active_only:
            # Only get predictions that haven't expired
            now = datetime.datetime.now()
            query['$or'] = [
                {'expires_at': {'$gt': now}},
                {'expires_at': None}
            ]
            
        return list(
            ai_prediction_collection.find(query)
            .sort('created_at', -1)
        )
    
    @staticmethod
    def mark_converted(prediction_id, task_id):
        """Mark a prediction as converted to a task"""
        if isinstance(prediction_id, str):
            try:
                prediction_id = ObjectId(prediction_id)
            except:
                return False
                
        result = ai_prediction_collection.update_one(
            {'_id': prediction_id},
            {'$set': {'converted_to_task': task_id}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def provide_feedback(prediction_id, was_accurate):
        """Provide feedback on prediction accuracy"""
        if isinstance(prediction_id, str):
            try:
                prediction_id = ObjectId(prediction_id)
            except:
                return False
                
        result = ai_prediction_collection.update_one(
            {'_id': prediction_id},
            {'$set': {'was_accurate': was_accurate}}
        )
        
        return result.modified_count > 0