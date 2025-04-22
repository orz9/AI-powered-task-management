import os
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import json
import base64

import openai
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Client class for interacting with OpenAI APIs (GPT and Whisper)
    """
    
    def __init__(self):
        """Initialize the OpenAI client with API key and configure settings"""
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _handle_api_error(self, error, attempt: int) -> bool:
        """
        Handle API errors with appropriate retry logic
        
        Args:
            error: The exception that was raised
            attempt: Current attempt number
            
        Returns:
            bool: True if should retry, False otherwise
        """
        if isinstance(error, openai.RateLimitError):
            wait_time = min(2 ** attempt * self.retry_delay, 60)  # Exponential backoff, max 60s
            logger.warning(f"Rate limit reached. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            return True
            
        elif isinstance(error, openai.APITimeoutError):
            wait_time = min(2 ** attempt * self.retry_delay, 30)
            logger.warning(f"API timeout. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            return True
            
        elif isinstance(error, openai.APIConnectionError):
            if attempt < self.max_retries:
                wait_time = self.retry_delay
                logger.warning(f"API connection error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                return True
                
        # Log all errors
        logger.error(f"OpenAI API error: {type(error).__name__}: {str(error)}")
        return False
        
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dict with transcription results
        """
        for attempt in range(self.max_retries):
            try:
                with open(audio_file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-1",
                        response_format="verbose_json",
                        timestamp_granularities=["word"]
                    )
                    
                return {
                    "text": response.text,
                    "segments": response.segments if hasattr(response, 'segments') else [],
                    "language": response.language if hasattr(response, 'language') else None
                }
                    
            except Exception as e:
                if not self._handle_api_error(e, attempt):
                    raise
                    
        # If all retries failed
        raise Exception(f"Failed to transcribe audio after {self.max_retries} attempts")
    
    def extract_tasks_from_text(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Extract tasks from transcribed text using GPT
        
        Args:
            text: Transcribed text to analyze
            context: Additional context about users, projects, etc.
            
        Returns:
            List of extracted tasks with details
        """
        system_prompt = """
        You are an AI assistant that extracts actionable tasks from meeting transcripts or notes.
        For each task you identify, extract the following information:
        - Task title (clear and concise)
        - Assigned person (if mentioned)
        - Due date (if mentioned)
        - Priority (if mentioned)
        - Description with any relevant details
        
        Format each task as a JSON object. Return only a valid JSON array of these task objects.
        DO NOT include any explanation, comments, or markdown. Example format:
        [
          {
            "title": "Prepare slides",
            "Assigned_person": "David",
            "description": "Create a slide deck for the weekly meeting",
            "due_date": "2025-04-30",
            "priority": "high"
          }
        ]
        """
        
        user_message = text
        
        if context:
            # Add context information to help with task extraction
            context_prompt = "Here is some context about the people and projects mentioned:\n"
            
            if 'people' in context:
                context_prompt += "People:\n"
                for person in context['people']:
                    context_prompt += f"- {person['name']} (Role: {person.get('role', 'Unknown')})\n"
                    
            if 'projects' in context:
                context_prompt += "Projects:\n"
                for project in context['projects']:
                    context_prompt += f"- {project['name']} (Status: {project.get('status', 'Unknown')})\n"
            
            user_message = context_prompt + "\n\nTranscript/Notes:\n" + text
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",  # Or use "gpt-4" for better results
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3  # Lower temperature for more consistent extraction
                )
                
                raw_content = response.choices[0].message.content.strip()
                logger.debug(f"Raw GPT response:\n{raw_content}")

                # Optional: try to extract the JSON part using regex if GPT still includes extra text
                if not raw_content.startswith("["):
                    import re
                    match = re.search(r"\[.*\]", raw_content, re.DOTALL)
                    if match:
                        raw_content = match.group(0)
                    else:
                        raise ValueError("Could not find valid JSON array in GPT response.")

                return json.loads(raw_content)
                
            except Exception as e:
                if not self._handle_api_error(e, attempt):
                    raise
        
        # If all retries failed
        raise Exception(f"Failed to extract tasks after {self.max_retries} attempts")
    
    def predict_upcoming_tasks(self, person_data: Dict[str, Any], historical_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict upcoming tasks for a person based on historical data
        
        Args:
            person_data: Data about the person
            historical_tasks: Historical task data for the person
            
        Returns:
            List of predicted tasks
        """
        # Prepare the historical task data in a format suitable for the model
        task_history_text = ""
        for task in historical_tasks[-20:]:  # Limit to most recent 20 tasks
            completed = task.get('completedAt', None) is not None
            status = "Completed" if completed else task.get('status', 'Pending')
            
            task_history_text += f"- {task['title']} ({status})\n"
            task_history_text += f"  Due: {task.get('dueDate', 'Not specified')}\n"
            task_history_text += f"  Priority: {task.get('priority', 'Not specified')}\n"
            if completed:
                task_history_text += f"  Completed on: {task.get('completedAt')}\n"
            task_history_text += "\n"
        
        # Prepare person data
        person_text = f"Name: {person_data['name']}\n"
        person_text += f"Role: {person_data.get('role', 'Not specified')}\n"
        
        if 'skills' in person_data:
            person_text += "Skills: " + ", ".join(person_data['skills']) + "\n"
            
        if 'teams' in person_data and person_data['teams']:
            person_text += "Teams: " + ", ".join([team.get('name', str(team.get('_id', ''))) 
                                                 for team in person_data['teams']]) + "\n"
        
        # Create system prompt
        system_prompt = """
        You are an AI assistant that predicts upcoming tasks for people based on their role,
        responsibilities, and task history. Analyze patterns in their previous tasks to predict
        new tasks they might need to complete, including recurring tasks, follow-ups, and
        logical next steps based on their work patterns.
        
        For each predicted task, include:
        - Task title
        - Estimated due date
        - Priority level
        - Brief description explaining why this task is predicted
        - Confidence score (0.0-1.0) with one decimal place to indicate your confidence in this prediction
        
        Format each task as a JSON object. Return only a valid JSON array of these task predictions.
        DO NOT include any explanation, comments, or markdown. Example format:
        [
          {
            "title": "Prepare slides",
            "description": "Create a slide deck for the weekly meeting",
            "estimated_due_date": "2025-04-30",
            "priority": "high",
            "confidence": "0.8"
          }
        ]
        """
        
        user_message = f"""
        ## Person Information
        {person_text}
        
        ## Recent Task History
        {task_history_text}
        
        Based on this information, predict what tasks this person is likely to need to complete 
        in the coming days and weeks. Consider recurring patterns, follow-ups to completed tasks,
        and tasks that logically follow from their current work and role.
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",  # Use GPT-4 for better predictions
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.5  # Balance between creativity and consistency
                )
                
                result = json.loads(response.choices[0].message.content)
                
                # Process and validate the predicted tasks
                predicted_tasks = result.get('tasks', [])
                for task in predicted_tasks:
                    # Ensure confidence score exists and is in proper range
                    if 'confidence' not in task or not isinstance(task['confidence'], (int, float)):
                        task['confidence'] = 0.7  # Default confidence
                    elif task['confidence'] < 0 or task['confidence'] > 1:
                        task['confidence'] = max(0, min(1, task['confidence']))  # Clamp to [0,1]
                        
                    # Add metadata
                    task['aiGenerated'] = True
                    task['source'] = 'prediction'
                    
                return predicted_tasks
                
            except Exception as e:
                if not self._handle_api_error(e, attempt):
                    raise
        
        # If all retries failed
        raise Exception(f"Failed to predict tasks after {self.max_retries} attempts")
    
    def analyze_tasks_for_insights(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze tasks to discover patterns and provide insights
        
        Args:
            tasks: List of task data to analyze
            
        Returns:
            Dictionary of insights and patterns
        """
        if not tasks:
            return {"insights": [], "error": "No tasks provided for analysis"}
            
        # Convert tasks to text for analysis
        tasks_text = ""
        for i, task in enumerate(tasks):
            tasks_text += f"{i+1}. {task['title']}\n"
            tasks_text += f"   Status: {task.get('status', 'Unknown')}\n"
            tasks_text += f"   Priority: {task.get('priority', 'Unknown')}\n"
            tasks_text += f"   Created: {task.get('createdAt', 'Unknown')}\n"
            tasks_text += f"   Due: {task.get('dueDate', 'Unknown')}\n"
            if task.get('completedAt'):
                tasks_text += f"   Completed: {task['completedAt']}\n"
            tasks_text += "\n"
        
        system_prompt = """
        You are an AI assistant that analyzes task data to identify patterns, bottlenecks,
        efficiency improvements, and other insights. Analyze the tasks provided to discover:
        
        1. Time management patterns (when tasks are created vs completed)
        2. Bottlenecks and delays in task completion
        3. Task distribution and workload balance
        4. Priority patterns and their impact on completion
        5. Efficiency recommendations
        
        Format your response as a JSON object with keys for each category of insight.
        Each insight should include a description and confidence level (0.0-1.0).

        Return only a valid JSON array of these task predictions.
        DO NOT include any explanation, comments, or markdown. Example format:
        {
          "time_management_patterns": {
            "description": "Most tasks are created early in the week but tend to be completed close to deadlines.",
            "confidence": 0.85
          },
          "bottlenecks_and_delays": {
            "description": "Tasks with high priority tend to be delayed due to workload clustering on specific individuals.",
            "confidence": 0.76
          },
          "task_distribution": {
            "description": "Workload is unevenly distributed, with one team member completing 60% of tasks.",
            "confidence": 0.82
          },
          "priority_impact": {
            "description": "High-priority tasks have slightly better completion rates but longer durations.",
            "confidence": 0.71
          },
          "efficiency_recommendations": {
            "description": "Consider balancing workload across team members and assigning deadlines earlier in the week.",
            "confidence": 0.88
          }
        }
        """
        
        user_message = f"""
        Please analyze the following tasks to identify patterns and provide insights:
        
        {tasks_text}
        
        Focus on practical, actionable insights that can help improve productivity and task management.
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3
                )
                
                return json.loads(response.choices[0].message.content)
                
            except Exception as e:
                if not self._handle_api_error(e, attempt):
                    raise
        
        # If all retries failed
        raise Exception(f"Failed to analyze tasks after {self.max_retries} attempts")
