import os
import json
import time
import logging
from datetime import timedelta
import openai
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg
from .models import Task, User, Team, TranscriptionRecord, AITaskPrediction

# Configure logger
logger = logging.getLogger(__name__)

# Initialize OpenAI API
openai.api_key = settings.OPENAI_API_KEY


def process_audio_with_whisper(audio_file):
    """
    Process audio file with OpenAI's Whisper API.
    
    Args:
        audio_file: The uploaded audio file
    
    Returns:
        tuple: (transcript text, confidence score, duration in seconds)
    """
    try:
        # Save the file temporarily if it's an in-memory file
        temp_filename = f"temp_audio_{int(time.time())}.mp3"
        with open(temp_filename, 'wb+') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
        
        # Call Whisper API
        with open(temp_filename, 'rb') as audio:
            response = openai.Audio.transcribe(
                file=audio,
                model="whisper-1",
                response_format="verbose_json",
                temperature=0.2
            )
        
        # Get transcript and metadata
        transcript = response['text']
        
        # Calculate an aggregate confidence score (average of segment confidences)
        segments = response.get('segments', [])
        if segments:
            confidence = sum(segment.get('confidence', 0) for segment in segments) / len(segments)
        else:
            confidence = 0.8  # Default if no segments
            
        # Get duration
        duration = response.get('duration', 0)
        
        # Clean up temp file
        os.remove(temp_filename)
        
        return transcript, confidence, duration
        
    except Exception as e:
        logger.error(f"Error processing audio with Whisper: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise
        

def extract_tasks_from_transcript(transcript, user):
    """
    Use GPT to extract tasks from a meeting transcript.
    
    Args:
        transcript: The transcript text
        user: The user who created the transcription
    
    Returns:
        list: List of created Task objects
    """
    try:
        # Prepare prompt for GPT
        prompt = f"""
        Extract actionable tasks from the following meeting transcript. 
        For each task, identify:
        1. Task title (brief summary)
        2. Detailed description
        3. Who it's assigned to (if mentioned)
        4. Due date (if mentioned)
        5. Priority level (if mentioned)
        
        Format your response as JSON with an array of task objects.
        
        Transcript:
        {transcript}
        """
        
        # Call GPT API
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            temperature=0.3,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Extract JSON from response
        task_data = []
        try:
            # Find JSON in the response
            text_response = response.choices[0].text.strip()
            # Extract JSON part (in case there's additional text)
            json_start = text_response.find('[')
            json_end = text_response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text_response[json_start:json_end]
                task_data = json.loads(json_str)
            else:
                # Try to extract JSON object if not an array
                json_start = text_response.find('{')
                json_end = text_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text_response[json_start:json_end]
                    task_obj = json.loads(json_str)
                    if isinstance(task_obj, dict):
                        task_data = [task_obj]
        except json.JSONDecodeError:
            logger.warning(f"JSON parsing failed, using regex to extract tasks")
            # Fallback to simple extraction if JSON parsing fails
            import re
            # Simple regex to find task titles
            task_titles = re.findall(r"Task:?\s*([^\n]+)", text_response)
            task_data = [{"title": title, "description": title} for title in task_titles]
            
        # Create Task objects
        created_tasks = []
        for task_item in task_data:
            # Clean and extract data
            title = task_item.get('title', '')[:200]  # Limit to model field size
            description = task_item.get('description', '')
            
            # Handle assignee if mentioned
            assignee = None
            assignee_name = task_item.get('assigned_to')
            if assignee_name:
                # Try to find user by name (simple match)
                try:
                    # Look for users with name containing the assignee_name
                    assignee = User.objects.filter(
                        username__icontains=assignee_name
                    ).first() or User.objects.filter(
                        first_name__icontains=assignee_name.split()[0] 
                        if ' ' in assignee_name else assignee_name
                    ).first()
                except:
                    pass
            
            # Parse priority
            priority = 2  # Default medium priority
            priority_text = task_item.get('priority', '').lower()
            if 'high' in priority_text or 'critical' in priority_text:
                priority = 3
            elif 'low' in priority_text:
                priority = 1
                
            # Parse due date
            due_date = None
            due_date_text = task_item.get('due_date')
            if due_date_text:
                try:
                    # Try common date formats and relative dates
                    from dateutil import parser
                    if 'tomorrow' in due_date_text.lower():
                        due_date = timezone.now() + timezone.timedelta(days=1)
                    elif 'next week' in due_date_text.lower():
                        due_date = timezone.now() + timezone.timedelta(days=7)
                    elif 'next month' in due_date_text.lower():
                        due_date = timezone.now() + timezone.timedelta(days=30)
                    else:
                        # Try to parse the date string
                        parsed_date = parser.parse(due_date_text)
                        due_date = timezone.make_aware(parsed_date)
                except:
                    logger.warning(f"Could not parse due date: {due_date_text}")
            
            # Create the task
            task = Task.objects.create(
                title=title,
                description=description,
                assigned_to=assignee,
                assigned_by=user,
                priority=priority,
                due_date=due_date,
                ai_generated=True,
                ai_confidence_score=0.85  # Default confidence
            )
            
            created_tasks.append(task)
            
        return created_tasks
        
    except Exception as e:
        logger.error(f"Error extracting tasks from transcript: {str(e)}")
        return []


def generate_task_predictions_with_gpt(user):
    """
    Generate task predictions for a user based on their history.
    
    Args:
        user: The User object to generate predictions for
    
    Returns:
        list: List of prediction dictionaries with text and confidence
    """
    try:
        # Gather context about the user
        recent_tasks = Task.objects.filter(assigned_to=user).order_by('-created_at')[:10]
        
        # Get team context
        teams = user.teams.all()
        team_members = []
        for team in teams:
            team_members.extend([member.username for member in team.members.all() 
                                if member != user])
        
        # Get task patterns
        common_categories = Task.objects.filter(assigned_to=user).values(
            'category__name'
        ).annotate(count=Count('id')).order_by('-count')[:3]
        
        recurring_patterns = []
        # Look for weekly patterns (same day of week)
        for day in range(7):
            day_count = Task.objects.filter(
                assigned_to=user, 
                created_at__week_day=day
            ).count()
            if day_count > 3:  # If there are several tasks on the same day of week
                recurring_patterns.append(f"Tasks often created on day {day} of the week")
        
        # Build context for GPT
        context = {
            "user": user.username,
            "recent_tasks": [
                {
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "due_date": task.due_date.isoformat() if task.due_date else None
                } for task in recent_tasks
            ],
            "teams": [team.name for team in teams],
            "team_members": team_members,
            "common_categories": [cat["category__name"] for cat in common_categories if cat["category__name"]],
            "recurring_patterns": recurring_patterns
        }
        
        # Create prompt for GPT
        prompt = f"""
        Based on the following context about a user, predict 3-5 upcoming tasks they might need to work on in the near future.
        
        User Context:
        {json.dumps(context, indent=2)}
        
        For each predicted task, provide:
        1. A clear title and description
        2. A confidence score (0.0-1.0) indicating how confident you are in this prediction
        3. Reasoning for why this task is likely needed
        
        Format your response as a JSON array of task prediction objects.
        """
        
        # Call GPT API
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Parse the response
        try:
            # Extract JSON
            text_response = response.choices[0].text.strip()
            json_start = text_response.find('[')
            json_end = text_response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = text_response[json_start:json_end]
                predictions = json.loads(json_str)
                
                # Format predictions
                formatted_predictions = []
                for pred in predictions:
                    text = f"{pred.get('title', 'Upcoming Task')}: {pred.get('description', '')}"
                    if 'reasoning' in pred:
                        text += f"\n\nRationale: {pred['reasoning']}"
                        
                    formatted_predictions.append({
                        'text': text,
                        'confidence': float(pred.get('confidence', 0.7))
                    })
                    
                return formatted_predictions
                
            else:
                # Fallback if JSON parsing fails
                logger.warning("Could not extract JSON from GPT response, using plain text")
                lines = text_response.split('\n')
                tasks = []
                current_task = ""
                
                for line in lines:
                    if line.strip().startswith("Task") or line.strip().startswith("1.") or line.strip().startswith("2."):
                        if current_task:
                            tasks.append(current_task)
                        current_task = line
                    else:
                        current_task += " " + line
                        
                if current_task:
                    tasks.append(current_task)
                    
                return [{'text': task, 'confidence': 0.7} for task in tasks if task.strip()]
                
        except Exception as parsing_error:
            logger.error(f"Error parsing GPT response: {str(parsing_error)}")
            # Return basic prediction as fallback
            return [{
                'text': "Follow up on recent tasks based on your work history.",
                'confidence': 0.6
            }]
            
    except Exception as e:
        logger.error(f"Error generating task predictions: {str(e)}")
        return [{
            'text': "Error generating predictions. Please try again later.",
            'confidence': 0.5
        }]


def handle_transcription_errors(transcript, confidence_score):
    """
    Handle and potentially correct transcription errors from Whisper.
    
    Args:
        transcript: The original transcript text
        confidence_score: The confidence score from Whisper
    
    Returns:
        str: Potentially corrected transcript
    """
    # If confidence is high, just return the transcript
    if confidence_score > 0.85:
        return transcript
        
    try:
        # For low confidence transcriptions, use GPT to improve quality
        prompt = f"""
        The following is a potentially inaccurate transcription of a meeting. 
        Please fix any obvious errors, fill in [inaudible] parts if you can guess them contextually,
        and make the text more coherent while preserving the meaning.
        
        Original transcription (confidence: {confidence_score}):
        {transcript}
        
        Corrected transcription:
        """
        
        # Call GPT API
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=len(transcript.split()) * 2,  # Double the tokens to allow for corrections
            temperature=0.3,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        corrected_transcript = response.choices[0].text.strip()
        return corrected_transcript
        
    except Exception as e:
        logger.error(f"Error correcting transcript: {str(e)}")
        return transcript  # Return original on error
