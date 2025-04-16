import axios from 'axios';

const AI_API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/ai';

// Configure axios with authentication
const aiApiClient = axios.create({
  baseURL: AI_API_BASE_URL,
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

// Process audio recording for transcription and task extraction
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
      `${AI_API_BASE_URL}/process-audio/`, 
      formData,
      config
    );
    return response.data;
  } catch (error) {
    console.error('Error processing audio transcription:', error);
    throw error;
  }
};

// Get AI-based task predictions
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

// Analyze past tasks for insights
export const getTaskAnalysis = async (personId, timeframe = 'month') => {
  try {
    const response = await aiApiClient.get(`/analyze-tasks/${personId}/?timeframe=${timeframe}`);
    return response.data;
  } catch (error) {
    console.error('Error analyzing tasks:', error);
    throw error;
  }
};