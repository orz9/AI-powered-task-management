import os
import json
import logging
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
from bson import ObjectId

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .openai_client import OpenAIClient
from tasks.models import tasks_collection
from people.models import MongoUser  # Updated to use MongoUser

# Access MongoDB collections
people_collection = settings.MONGODB_DB['people']
ai_training_data_collection = settings.MONGODB_DB['ai_training_data']

logger = logging.getLogger(__name__)

class ProcessAudioView(APIView):
    """
    API endpoint for processing audio recordings to extract tasks
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        if 'audio' not in request.FILES:
            return Response(
                {"error": "No audio file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        audio_file = request.FILES['audio']
        user_id = request.data.get('userId')
        
        # Save the uploaded file to a temporary location
        with NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Initialize the OpenAI client
            openai_client = OpenAIClient()
            
            # Transcribe the audio
            transcription_result = openai_client.transcribe_audio(tmp_file_path)
            
            # Fetch context for task extraction
            context = self._get_context_for_user(user_id)
            
            # Extract tasks from the transcription
            extracted_tasks = openai_client.extract_tasks_from_text(
                transcription_result['text'],
                context
            )
            
            # Process and format extracted tasks
            processed_tasks = self._process_extracted_tasks(extracted_tasks, user_id)
            
            # Store transcription and extraction as training data
            self._store_training_data(
                user_id,
                'speech_transcription',
                {
                    'transcription': transcription_result['text'],
                    'extracted_tasks': extracted_tasks
                }
            )
            
            return Response({
                'transcription': transcription_result['text'],
                'extractedTasks': processed_tasks
            })
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return Response(
                {"error": f"Error processing audio: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    def _get_context_for_user(self, user_id):
        """Get relevant context for the given user to improve task extraction"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id_obj = ObjectId(user_id)
                except:
                    logger.warning(f"Invalid user ID format: {user_id}")
                    return {}
            else:
                user_id_obj = user_id
                
            # Get the person associated with the user
            person = people_collection.find_one({'userId': user_id_obj})
            
            if not person:
                logger.warning(f"Person not found for user {user_id}")
                return {}
                
            # Get colleagues/related people
            related_people = list(people_collection.find({
                'organization': person['organization'],
                '_id': {'$ne': person['_id']}
            }).limit(10))  # Limit to 10 people
            
            # Format context data
            context = {
                'people': [
                    {
                        'id': str(p['_id']),
                        'name': p.get('name', ''),
                        'role': p.get('role', '')
                    } for p in [person] + related_people
                ]
            }
            
            # Add projects if available
            # (Implementation depends on your project model)
            
            return context
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return {}
    
    def _process_extracted_tasks(self, extracted_tasks, user_id):
        """Process and format extracted tasks"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id_obj = ObjectId(user_id)
                except:
                    logger.warning(f"Invalid user ID format: {user_id}")
                    return extracted_tasks  # Return unprocessed tasks
            else:
                user_id_obj = user_id
                
            # Get the person associated with the user
            person = people_collection.find_one({'userId': user_id_obj})
            
            if not person:
                logger.warning(f"Person not found for user {user_id}")
                return extracted_tasks  # Return unprocessed tasks
                
            processed_tasks = []
            for task in extracted_tasks:
                # Look up the assigned person by name if provided
                assigned_to = None
                if 'assigned_person' in task and task['assigned_person']:
                    try:
                        assigned_person = people_collection.find_one({
                            'name': {'$regex': task['assigned_person'], '$options': 'i'},
                            'organization': person['organization']
                        })
                        
                        if assigned_person:
                            assigned_to = str(assigned_person['_id'])
                    except Exception as e:
                        logger.error(f"Error looking up assigned person: {str(e)}")
                
                # Default to the current user if no assignee found
                if not assigned_to:
                    assigned_to = str(person['_id'])
                
                # Format the due date if provided
                due_date = None
                if 'due_date' in task and task['due_date']:
                    try:
                        # This would need more sophisticated date parsing in production
                        # For now, a simple approach
                        if 'tomorrow' in task['due_date'].lower():
                            due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                        elif 'next week' in task['due_date'].lower():
                            due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        # Add more date parsing as needed
                    except Exception as e:
                        logger.error(f"Error parsing due date: {str(e)}")
                
                # Format the processed task
                processed_task = {
                    'title': task.get('title', 'Untitled Task'),
                    'description': task.get('description', ''),
                    'assignedTo': assigned_to,
                    'dueDate': due_date,
                    'priority': task.get('priority', 'medium').lower(),
                    'source': 'transcription'
                }
                
                processed_tasks.append(processed_task)
            
            return processed_tasks
            
        except Exception as e:
            logger.error(f"Error processing extracted tasks: {str(e)}")
            return extracted_tasks
    
    def _store_training_data(self, user_id, data_type, data):
        """Store data for AI training and improvement"""
        try:
            # Convert user_id to ObjectId if it's a string
            if isinstance(user_id, str):
                try:
                    user_id_obj = ObjectId(user_id)
                except:
                    logger.warning(f"Invalid user ID format: {user_id}")
                    return
            else:
                user_id_obj = user_id
                
            person = people_collection.find_one({'userId': user_id_obj})
            
            if not person:
                logger.warning(f"Person not found for user {user_id}")
                return
                
            # Insert training data
            ai_training_data_collection.insert_one({
                'personId': person['_id'],
                'dataType': data_type,
                'data': data,
                'createdAt': datetime.now()
            })
        except Exception as e:
            logger.error(f"Error storing training data: {str(e)}")


class PredictTasksView(APIView):
    """
    API endpoint for predicting upcoming tasks
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    def post(self, request, format=None):
        person_id = request.data.get('personId')
        context_data = request.data.get('contextData', {})
        
        if not person_id:
            return Response(
                {"error": "Person ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert person_id to ObjectId
            try:
                person_id_obj = ObjectId(person_id)
            except:
                return Response(
                    {"error": "Invalid person ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get person data
            person = people_collection.find_one({'_id': person_id_obj})
            
            if not person:
                return Response(
                    {"error": "Person not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            person_data = {
                'id': str(person['_id']),
                'name': person.get('name', ''),
                'role': person.get('role', ''),
                'skills': person.get('skills', []),
                'teams': []
            }
            
            # Get teams for the person
            if 'teams' in person:
                team_ids = person['teams']
                teams = []
                for team_id in team_ids:
                    team = settings.MONGODB_DB['teams'].find_one({'_id': team_id})
                    if team:
                        teams.append({
                            '_id': str(team['_id']),
                            'name': team.get('name', '')
                        })
                person_data['teams'] = teams
            
            # Get historical task data
            historical_tasks = []
            tasks = list(tasks_collection.find(
                {'assignedTo': person_id_obj}
            ).sort('createdAt', -1).limit(50))
            
            for task in tasks:
                task_data = {
                    'id': str(task['_id']),
                    'title': task.get('title', ''),
                    'description': task.get('description', ''),
                    'status': task.get('status', ''),
                    'priority': task.get('priority', ''),
                    'dueDate': task.get('dueDate', '').strftime('%Y-%m-%d') if 'dueDate' in task and task['dueDate'] else None,
                    'createdAt': task.get('createdAt', '').strftime('%Y-%m-%d') if 'createdAt' in task and task['createdAt'] else None,
                    'completedAt': task.get('completedAt', '').strftime('%Y-%m-%d') if 'completedAt' in task and task['completedAt'] else None
                }
                historical_tasks.append(task_data)
            
            # Get predictions from OpenAI
            openai_client = OpenAIClient()
            predicted_tasks = openai_client.predict_upcoming_tasks(person_data, historical_tasks)
            
            # Process predictions for response
            processed_predictions = []
            for task in predicted_tasks:
                processed_task = {
                    'title': task.get('title', 'Untitled Task'),
                    'description': task.get('description', ''),
                    'dueDate': task.get('due_date') or task.get('dueDate'),
                    'priority': task.get('priority', 'medium').lower(),
                    'confidence': task.get('confidence', 0.7),
                    'assignedTo': str(person['_id']),
                    'aiGenerated': True
                }
                processed_predictions.append(processed_task)
            
            return Response({
                'predictedTasks': processed_predictions
            })
            
        except Exception as e:
            logger.error(f"Error predicting tasks: {str(e)}")
            return Response(
                {"error": f"Error predicting tasks: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnalyzeTasksView(APIView):
    """
    API endpoint for analyzing tasks and providing insights
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, person_id, format=None):
        timeframe = request.query_params.get('timeframe', 'month')
        
        # Determine date range based on timeframe
        now = datetime.now()
        if timeframe == 'week':
            start_date = now - timedelta(days=7)
        elif timeframe == 'month':
            start_date = now - timedelta(days=30)
        elif timeframe == 'quarter':
            start_date = now - timedelta(days=90)
        elif timeframe == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # Default to month
        
        try:
            # Convert person_id to ObjectId
            try:
                person_id_obj = ObjectId(person_id)
            except:
                return Response(
                    {"error": "Invalid person ID format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get tasks for the person within the timeframe
            tasks = list(tasks_collection.find({
                'assignedTo': person_id_obj,
                'createdAt': {'$gte': start_date}
            }).sort('createdAt', -1))
            
            # Convert tasks to dict format for analysis
            task_data = []
            for task in tasks:
                task_dict = {
                    'id': str(task['_id']),
                    'title': task.get('title', ''),
                    'description': task.get('description', ''),
                    'status': task.get('status', ''),
                    'priority': task.get('priority', ''),
                    'dueDate': task.get('dueDate', '').strftime('%Y-%m-%d') if 'dueDate' in task and task['dueDate'] else None,
                    'createdAt': task.get('createdAt', '').strftime('%Y-%m-%d') if 'createdAt' in task and task['createdAt'] else None,
                    'completedAt': task.get('completedAt', '').strftime('%Y-%m-%d') if 'completedAt' in task and task['completedAt'] else None
                }
                task_data.append(task_dict)
            
            if not task_data:
                return Response({
                    'insights': [],
                    'message': 'Not enough task data for analysis'
                })
            
            # Get insights from OpenAI
            openai_client = OpenAIClient()
            insights = openai_client.analyze_tasks_for_insights(task_data)
            
            return Response(insights)
            
        except Exception as e:
            logger.error(f"Error analyzing tasks: {str(e)}")
            return Response(
                {"error": f"Error analyzing tasks: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SaveExtractedTasksView(APIView):
    """
    API endpoint for saving tasks extracted from audio
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    def post(self, request, format=None):
        tasks_data = request.data.get('tasks', [])
        
        if not tasks_data:
            return Response(
                {"error": "No tasks provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            created_tasks = []
            
            for task_data in tasks_data:
                # Convert string IDs to ObjectId
                if 'assignedTo' in task_data and task_data['assignedTo']:
                    task_data['assignedTo'] = ObjectId(task_data['assignedTo'])
                    
                # Get user's person record
                person = people_collection.find_one({'userId': ObjectId(str(request.user.id))})
                if not person:
                    return Response(
                        {"error": "User's person record not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Create new task document
                new_task = {
                    'title': task_data.get('title', 'Untitled Task'),
                    'description': task_data.get('description', ''),
                    'status': 'pending',
                    'priority': task_data.get('priority', 'medium'),
                    'assignedTo': task_data.get('assignedTo'),
                    'assignedBy': person['_id'],
                    'organization': person['organization'],
                    'source': task_data.get('source', 'transcription'),
                    'aiGenerated': task_data.get('aiGenerated', False),
                    'createdAt': datetime.now(),
                    'updatedAt': datetime.now()
                }
                
                # Set due date if provided
                if 'dueDate' in task_data and task_data['dueDate']:
                    try:
                        new_task['dueDate'] = datetime.strptime(task_data['dueDate'], '%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Invalid due date format: {task_data['dueDate']}")
                
                # Insert task
                result = tasks_collection.insert_one(new_task)
                
                created_tasks.append({
                    'id': str(result.inserted_id),
                    'title': new_task['title']
                })
            
            return Response({
                'message': f"Successfully created {len(created_tasks)} tasks",
                'tasks': created_tasks
            })
            
        except Exception as e:
            logger.error(f"Error saving tasks: {str(e)}")
            return Response(
                {"error": f"Error saving tasks: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )