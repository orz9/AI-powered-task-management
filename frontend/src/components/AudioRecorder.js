import React, { useState, useRef, useEffect } from 'react';
import { processAudioTranscription } from '../api/aiApi';
import { createTask } from '../api/taskApi';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const AudioRecorder = ({ userId, people: initialPeople }) => {
  const { currentUser } = useAuth();
  const [people, setPeople] = useState(initialPeople || []);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedTasks, setExtractedTasks] = useState([]);
  const [error, setError] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  
  // Fetch people directly from API
  useEffect(() => {
    const fetchPeople = async () => {
      try {
        const token = localStorage.getItem('token');
        // First try to get people from API
        const response = await axios.get(`${API_BASE_URL}/people/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data && Array.isArray(response.data)) {
          console.log("People data from API:", response.data);
          setPeople(response.data);
        }
      } catch (err) {
        console.error('Error fetching people:', err);
        
        // If API fails, at least add current user
        if (currentUser) {
          const currentUserPerson = {
            id: currentUser.id,
            name: currentUser.name || currentUser.username || 'Current User',
            role: currentUser.role
          };
          console.log("Adding current user as fallback:", currentUserPerson);
          setPeople([currentUserPerson]);
        }
      }
    };

    fetchPeople();
  }, [currentUser]);

  // Set current user as assignee when currentUser or people changes
    useEffect(() => {
      if (currentUser && currentUser.id && people.length > 0) {
        // Find the current user in people list
        const currentUserInList = people.find(person => 
          person.id === currentUser.id || 
          person.email === currentUser.email
        );
        
        if (currentUserInList) {
          setExtractedTasks(prev =>
            prev?.map(task => ({
              ...task,
              assignedBy: currentUserInList.id
            })) || []
          );
        }
      }
    }, [currentUser, people, extractedTasks]);
  
    // Set current user as assignedBy
    useEffect(() => {
      if (currentUser && currentUser.id && people.length > 0) {
        // Find the current user in people list
        const currentUserInList = people.find(person => 
          person.id === currentUser.id || 
          person.email === currentUser.email
        );
  
        if (currentUserInList) {
          setExtractedTasks(prev =>
            prev?.map(task => ({
              ...task,
              assignedBy: currentUserInList.id
            })) || []
          );
        }
      }
    }, [currentUser, people, extractedTasks])
  
  // Clean up when component unmounts
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);
  
  // Start recording audio
  const startRecording = async () => {
    try {
      setError(null);
      setTranscription('');
      setExtractedTasks([]);
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
      
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
      };      
      
      // Start recording and timer
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);
      
    } catch (err) {
      setError('Permission to record audio was denied or another error occurred.');
      console.error('Error starting audio recording:', err);
    }
  };
  
  // Stop recording audio
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      // Clear the timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };
  
  // Format recording time
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };
  
  // Process audio for transcription and task extraction
  const processAudio = async () => {
    if (!audioBlob) return;
    
    setIsProcessing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('userId', userId || currentUser?.id);
      
      const response = await processAudioTranscription(formData);
      
      setTranscription(response.transcription);
      setExtractedTasks(response.extractedTasks || []);
      
      if (!(response.extractedTasks && response.extractedTasks.length > 0)) {
        setError('No tasks could be extracted. Try speaking more clearly about specific tasks.');
      }
    } catch (err) {
      console.error('Error processing audio:', err);
      setError('Error processing audio. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Save extracted tasks to database
  const saveTasks = async () => {
    if (!extractedTasks || extractedTasks.length === 0) {
      setError('No tasks to save');
      return;
    }
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Create each task
      for (const task of extractedTasks) {
        await createTask({
          ...task,
          status: 'todo',
          aiGenerated: true,
          source: 'audio'
        });
      }
      console.log("debug: ", extractedTasks);
      
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      
      // Clear tasks after saving
      setExtractedTasks([]);
    } catch (err) {
      console.error('Error saving tasks:', err);
      setError('Failed to save tasks. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="audio-recorder">
      <div className="recording-controls">
        {!isRecording ? (
          <button 
            className="start-recording-btn" 
            onClick={startRecording}
            disabled={isProcessing}
          >
            Start Recording
          </button>
        ) : (
          <button 
            className="stop-recording-btn" 
            onClick={stopRecording}
          >
            Stop Recording ({formatTime(recordingTime)})
          </button>
        )}
        
        {audioBlob && !isRecording && (
          <button 
            className="process-audio-btn" 
            onClick={processAudio}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Process Audio'}
          </button>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {showSuccess && (
        <div className="success-message">Tasks saved successfully!</div>
      )}
      
      {isProcessing && (
        <div className="processing-indicator">
          Processing audio...
        </div>
      )}
      
      {transcription && (
        <div className="transcription-result">
          <h3>Transcription:</h3>
          <p>{transcription}</p>
        </div>
      )}
      
      {extractedTasks.length > 0 && (
        <div className="extracted-tasks">
          <h3>Extracted Tasks:</h3>
          <div className="task-list">
            {extractedTasks.map((task, index) => (
              <div key={index} className="extracted-task-item">
                <h4 className="task-title">{task.title}</h4>
                {task.description && <p className="task-description">{task.description}</p>}
                <div className="task-details">
                  {task.assignedTo && <span>Assigned to: {task.assignedTo}</span>}
                  {task.dueDate && <span>Due date: {task.dueDate}</span>}
                  {task.priority && <span className={`priority-${task.priority}`}>Priority: {task.priority}</span>}
                </div>
              </div>
            ))}
          </div>
          
          <button 
            className="save-tasks-btn" 
            onClick={saveTasks}
            disabled={isProcessing}
          >
            Save Tasks
          </button>
        </div>
      )}
      
      {audioUrl && (
        <div className="audio-playback">
          <h3>Review Recording:</h3>
          <audio controls src={audioUrl} />
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;