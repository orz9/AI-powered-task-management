// src/api/taskApi.js
import axios from 'axios';

// IMPORTANT: Make sure this matches exactly what's in your environment variables
// or is the correct URL for your backend
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// Configure axios with authentication
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Fetch tasks for a user
 * @param {string} userId - User ID
 * @param {string} role - User role (leader, team_member)
 * @returns {Promise<Array>} - Tasks data
 */
export const fetchTasks = async (userId, role) => {
  try {
    let endpoint;
    
    if (role === 'leader') {
      endpoint = '/tasks/';
    } else {
      // If there's a 404 on /tasks/user/:id/, try alternative paths
      endpoint = `/tasks/?assignedTo=${userId}`;
    }
    
    console.log(`Fetching tasks from: ${endpoint}`);
    const response = await apiClient.get(endpoint);
    return response.data;
  } catch (error) {
    console.error('Error fetching tasks:', error);
    // Return empty array instead of throwing to prevent UI breaks
    return [];
  }
};

/**
 * Create a new task
 * @param {Object} taskData - Task data
 * @returns {Promise<Object>} - Created task
 */
export const createTask = async (taskData) => {
  try {
    console.log("Creating task with data:", taskData);
    
    // Ensure proper field names and formatting
    const formattedData = {
      title: taskData.title,
      description: taskData.description || "",
      status: taskData.status || "todo",
      priority: taskData.priority || "medium",
      assignedTo: taskData.assignedTo || null,
      assignedBy: taskData.assignedBy || null,
      team: taskData.team || null,
      dueDate: taskData.dueDate || null,
      aiGenerated: !!taskData.aiGenerated
    };
    
    console.log("Formatted request data:", formattedData);
    const response = await apiClient.post('/tasks/', formattedData);
    console.log("Response data:", response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating task:', error);
    console.error('Error response:', error.response?.data || 'No response data');
    throw error;
  }
};

/**
 * Update an existing task
 * @param {string} taskId - Task ID
 * @param {Object} taskData - Updated task data
 * @returns {Promise<Object>} - Updated task
 */
export const updateTask = async (taskId, taskData) => {
  try {
    // Log what we're about to send to the server
    console.log("Updating task:", taskId);
    console.log("Update data:", taskData);
    
    // Make sure we're matching the expected field names on the backend
    const formattedData = {
      title: taskData.title,
      description: taskData.description || "",
      status: taskData.status || "todo",
      priority: taskData.priority || "medium",
      dueDate: taskData.dueDate || null
    };
    
    // If you have assigning to a new person, include that
    if (taskData.assignedTo) {
      formattedData.assignedTo = taskData.assignedTo;
    }
    
    const response = await apiClient.put(`/tasks/${taskId}/`, formattedData);
    console.log("Update response:", response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating task:', error);
    console.error('Error response:', error.response?.data || 'No response data');
    throw error;
  }
};

/**
 * Delete a task
 * @param {string} taskId - Task ID to delete
 * @returns {Promise<boolean>} - Success status
 */
export const deleteTask = async (taskId) => {
  try {
    await apiClient.delete(`/tasks/${taskId}/`);
    return true;
  } catch (error) {
    console.error('Error deleting task:', error);
    throw error;
  }
};

/**
 * Get task details
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} - Task details
 */
export const getTaskDetails = async (taskId) => {
  try {
    const response = await apiClient.get(`/tasks/${taskId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching task details:', error);
    throw error;
  }
};

/**
 * Fetch people (users/teammates)
 * @param {string} userId - User ID
 * @param {string} role - User role (leader, team_member)
 * @returns {Promise<Array>} - People data
 */
export const fetchPeople = async (userId, role) => {
  try {
    // Use a more general endpoint to avoid 404s
    const endpoint = '/people/';
    console.log(`Fetching people from: ${endpoint}`);
    const response = await apiClient.get(endpoint);
    return response.data;
  } catch (error) {
    console.error('Error fetching people:', error);
    // Return default data to prevent UI breaks
    return [
      { id: userId, name: 'Current User' }
    ];
  }
};

/**
 * Fetch details about a specific person
 * @param {string} personId - Person ID
 * @returns {Promise<Object>} - Person details
 */
export const fetchPersonDetails = async (personId) => {
  try {
    const response = await apiClient.get(`/people/${personId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching person details:', error);
    return { id: personId, name: 'Unknown User' };
  }
};

/**
 * Fetch teams
 * @returns {Promise<Array>} - Teams data
 */
export const fetchTeams = async () => {
  try {
    const response = await apiClient.get('/teams/');
    return response.data;
  } catch (error) {
    console.error('Error fetching teams:', error);
    
    // For development/testing: Return mock data if API fails
    return [
      { id: '1', name: 'Development' },
      { id: '2', name: 'Design' },
      { id: '3', name: 'Marketing' }
    ];
  }
};

/**
 * Add comment to a task
 * @param {string} taskId - Task ID
 * @param {string} content - Comment text
 * @returns {Promise<Object>} - Created comment
 */
export const addTaskComment = async (taskId, content) => {
  try {
    const response = await apiClient.post(`/tasks/${taskId}/add_comment/`, { content });
    return response.data;
  } catch (error) {
    console.error('Error adding comment:', error);
    throw error;
  }
};

/**
 * Get task history
 * @param {string} taskId - Task ID
 * @returns {Promise<Array>} - Task history entries
 */
export const getTaskHistory = async (taskId) => {
  try {
    const response = await apiClient.get(`/tasks/${taskId}/history/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching task history:', error);
    return [];
  }
};