// src/api/aiApi.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// Configure axios with authentication
const aiApiClient = axios.create({
  baseURL: `${API_BASE_URL}/ai`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
aiApiClient.interceptors.request.use(
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
 * Process audio recording for transcription and task extraction
 * @param {FormData} formData - FormData object containing audio file and userId
 * @returns {Promise<Object>} - Transcription and extracted tasks
 */
export const processAudioTranscription = async (formData) => {
  try {
    // For form data, update headers
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    };
    
    const response = await axios.post(
      `${API_BASE_URL}/ai/process-audio/`, 
      formData,
      config
    );
    return response.data;
  } catch (error) {
    console.error('Error processing audio transcription:', error);
    throw error;
  }
};

/**
 * Get AI-based task predictions for a specific person
 * @param {string} personId - ID of the person to generate predictions for
 * @param {Object} contextData - Additional context data (optional)
 * @returns {Promise<Object>} - Predicted tasks
 */
export const getPredictedTasks = async (personId, contextData = {}) => {
  try {
    const response = await aiApiClient.post('/predict-tasks/', {
      personId,
      contextData
    });
    return response.data;
  } catch (error) {
    console.error('Error getting task predictions:', error);
    throw error;
  }
};

/**
 * Analyze past tasks for insights and patterns
 * @param {string} personId - ID of the person to analyze tasks for
 * @param {string} timeframe - Time period for analysis (week, month, quarter, year)
 * @returns {Promise<Object>} - Analysis results
 */
export const getTaskAnalysis = async (personId, timeframe = 'month') => {
  try {
    const response = await aiApiClient.get(`/analyze-tasks/${personId}/?timeframe=${timeframe}`);
    return response.data;
  } catch (error) {
    console.error('Error analyzing tasks:', error);
    throw error;
  }
};

/**
 * Save tasks extracted from audio
 * @param {Array} tasks - Array of task objects to save
 * @returns {Promise<Object>} - Response with created tasks info
 */
export const saveExtractedTasks = async (tasks) => {
  try {
    const response = await aiApiClient.post('/save-tasks/', { tasks });
    return response.data;
  } catch (error) {
    console.error('Error saving extracted tasks:', error);
    throw error;
  }
};