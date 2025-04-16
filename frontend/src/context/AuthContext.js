// src/context/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

// Create the context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provider component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Check if user is already logged in (token exists)
  useEffect(() => {
    const checkLoggedIn = async () => {
      setLoading(true);
      const token = localStorage.getItem('token');

      if (token) {
        try {
          // Validate token and get user data
          const response = await axios.get(`${API_BASE_URL}/auth/user/`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          setCurrentUser(response.data);
        } catch (err) {
          console.error('Error validating token:', err);
          localStorage.removeItem('token'); // Remove invalid token
          setCurrentUser(null);
        }
      }
      
      setLoading(false);
    };

    checkLoggedIn();
  }, []);

  // Login function
  const login = async (username, password) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/login/`, {
        username,
        password
      });
      
      const { token, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('token', token);
      
      // Set user data in state
      setCurrentUser(user);
      
      return true;
    } catch (err) {
      console.error('Login error:', err);
      
      setError(
        err.response?.data?.detail || 
        'Login failed. Please check your credentials and try again.'
      );
      
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  // Register function
  const register = async (userData) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/register/`, userData);
      
      const { token, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('token', token);
      
      // Set user data in state
      setCurrentUser(user);
      
      return true;
    } catch (err) {
      console.error('Registration error:', err);
      
      if (err.response?.data) {
        // Format validation errors
        const errors = err.response.data;
        let errorMessage = '';
        
        for (const key in errors) {
          errorMessage += `${key}: ${errors[key].join(', ')}\n`;
        }
        
        setError(errorMessage || 'Registration failed. Please try again.');
      } else {
        setError('Registration failed. Please try again.');
      }
      
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update user profile
  const updateProfile = async (profileData) => {
    setLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.patch(
        `${API_BASE_URL}/auth/user/`,
        profileData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setCurrentUser(response.data);
      return true;
    } catch (err) {
      console.error('Profile update error:', err);
      
      setError('Failed to update profile. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Reset password
  const resetPassword = async (email) => {
    setLoading(true);
    setError('');
    
    try {
      await axios.post(`${API_BASE_URL}/auth/password-reset/`, { email });
      return true;
    } catch (err) {
      console.error('Password reset error:', err);
      
      setError('Failed to request password reset. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Context value
  const value = {
    currentUser,
    loading,
    error,
    login,
    logout,
    register,
    updateProfile,
    resetPassword
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
