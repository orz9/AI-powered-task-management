import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { createTask } from '../api/taskApi';
import { useAuth } from '../context/AuthContext';
import AudioRecorder from './AudioRecorder';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const CreateTaskForm = ({ people: initialPeople, teams, onTaskCreated }) => {
  const { currentUser } = useAuth();
  const [people, setPeople] = useState(initialPeople || []);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    assignedTo: '',
    assignedBy: '',
    team: '',
    priority: 'medium',
    dueDate: '',
    status: 'todo'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [showVoiceModel, setShowVoiceModel] = useState(false);

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
        setFormData(prev => ({
          ...prev,
          assignedTo: currentUserInList.id
        }));
      }
    }
  }, [currentUser, people]);

  // Set current user as assignedBy
  useEffect(() => {
    if (currentUser && currentUser.id && people.length > 0) {
      // Find the current user in people list
      const currentUserInList = people.find(person => 
        person.id === currentUser.id || 
        person.email === currentUser.email
      );

      if (currentUserInList) {
        setFormData(prev => ({
          ...prev,
          assignedBy: currentUserInList.id
        }));
      }
    }
  }, [currentUser, people]) 

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Submit the form to create a new task
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    try {
      // Create task
      await createTask({
        ...formData,
        aiGenerated: false
      });
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      
      // Notify parent component
      if (onTaskCreated) {
        onTaskCreated();
      }
    } catch (err) {
      console.error('Error creating task:', err);
      setError('Failed to create task. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="create-task-form-container">
      <h3>Create New Task</h3>
      
      {error && <div className="error-message">{error}</div>}
      {showSuccess && <div className="success-message">Task created successfully!</div>}
      
      <form className="create-task-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Task Title*</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Enter task title"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="3"
            placeholder="Enter task description"
          />
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="assignedTo">Assigned To*</label>
            <select
              id="assignedTo"
              name="assignedTo"
              value={formData.assignedTo}
              onChange={handleChange}
              required
            >
              <option value="">Select a person</option>
              {people && people.length > 0 ? (
                people.map(person => (
                  <option key={person.id} value={person.id}>
                    {person.name || person.username}
                  </option>
                ))
              ) : (
                <option value="" disabled>No people available</option>
              )}
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="team">Team</label>
            <select
              id="team"
              name="team"
              value={formData.team}
              onChange={handleChange}
            >
              <option value="">None</option>
              {teams?.map(team => (
                <option key={team._id} value={team.name}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="status">Status</label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
            >
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="review">Review</option>
              <option value="done">Done</option>
            </select>
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="dueDate">Due Date</label>
          <input
            type="date"
            id="dueDate"
            name="dueDate"
            value={formData.dueDate}
            onChange={handleChange}
            min={new Date().toISOString().split('T')[0]}
          />
        </div>
        
        <div className="form-actions">
          <button
            type="submit"
            className="create-task-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating...' : 'Create Task'}
          </button>
          <button
            type="button"
            className="voice-create-btn"
            onClick={() => setShowVoiceModel(true)}
          >
            🎤 Voice Create
          </button>
        </div>
        
        {showVoiceModel && (
          <div className="voice-model-overlay">
            <div className="voice-model">
              <div className="voice-model-header">
                <h3>Create Task with Voice</h3>
                <button 
                  className="close-model-btn"
                  onClick={() => setShowVoiceModel(false)}
                >
                  &times;
                </button>
              </div>
              <div className="voice-model-content">
                <AudioRecorder 
                  userId={currentUser?.id}
                  onTasksCreated={() => {
                    setShowVoiceModel(false);
                    if (onTaskCreated) {
                      onTaskCreated();
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default CreateTaskForm;