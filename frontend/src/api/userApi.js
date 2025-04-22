// src/api/userApi.js
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
 * Get user profile details
 * @returns {Promise<Object>} - User profile data
 */
export const getUserProfile = async () => {
  try {
    const response = await apiClient.get('/auth/user/');
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

/**
 * Update user profile
 * @param {Object} profileData - Updated profile data
 * @returns {Promise<Object>} - Updated user profile
 */
export const updateUserProfile = async (profileData) => {
  try {
    const response = await apiClient.patch('/auth/user/', profileData);
    return response.data;
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

/**
 * Fetch available roles
 * @returns {Promise<Array>} - Available roles
 */
export const fetchRoles = async () => {
  try {
    const response = await apiClient.get('/roles/');
    return response.data;
  } catch (error) {
    console.error('Error fetching roles:', error);
    // Return mock data if API fails
    return [
      { id: '1', name: 'leader', permission_level: 3, description: 'Team leader with management abilities' },
      { id: '2', name: 'team_member', permission_level: 1, description: 'Regular team member' },
      { id: '3', name: 'admin', permission_level: 5, description: 'System administrator' }
    ];
  }
};

/**
 * Update user password
 * @param {Object} passwordData - Old and new password data
 * @returns {Promise<Object>} - Response data
 */
export const updatePassword = async (passwordData) => {
  try {
    const response = await apiClient.post('/auth/password/change/', passwordData);
    return response.data;
  } catch (error) {
    console.error('Error updating password:', error);
    throw error;
  }
};

export default {
  getUserProfile,
  updateUserProfile,
  fetchRoles,
  updatePassword
};