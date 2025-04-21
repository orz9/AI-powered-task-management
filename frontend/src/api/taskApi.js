// src/api/taskApi.js
import axios from 'axios';

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
    const endpoint = role === 'leader' ? '/tasks/' : `/tasks/user/${userId}/`;
    const response = await apiClient.get(endpoint);
    return response.data;
  } catch (error) {
    console.error('Error fetching tasks:', error);
    throw error;
  }
};

/**
 * Create a new task
 * @param {Object} taskData - Task data
 * @returns {Promise<Object>} - Created task
 */
export const createTask = async (taskData) => {
  try {
    console.log("Request data:", taskData);
    const response = await apiClient.post('/tasks/', taskData);
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
    const response = await apiClient.put(`/tasks/${taskId}/`, taskData);
    return response.data;
  } catch (error) {
    console.error('Error updating task:', error);
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
    const endpoint = role === 'leader' ? '/people/' : `/people/related/${userId}/`;
    const response = await apiClient.get(endpoint);
    return response.data;
  } catch (error) {
    console.error('Error fetching people:', error);
    throw error;
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
    throw error;
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
    throw error;
  }
};