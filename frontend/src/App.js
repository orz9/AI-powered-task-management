import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Components
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import CreateTaskForm from './components/CreateTaskForm';
import Navigation from './components/Navigation';
import TaskList from './components/TaskList';
import PeopleList from './components/PeopleList';

// CSS
import './styles/App.css';
import './styles/Navigation.css';
import './styles/Dashboard.css';

// Private Route component
const PrivateRoute = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }
  
  return currentUser ? children : <Navigate to="/login" />;
};

// Layout component with navigation
const PrivateLayout = ({ children }) => {
  return (
    <>
      <Navigation />
      <main className="main-content">
        {children}
      </main>
    </>
  );
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} /> {/* Add Register route */}
      <Route 
        path="/dashboard" 
        element={
          <PrivateRoute>
            <PrivateLayout>
              <Dashboard />
            </PrivateLayout>
          </PrivateRoute>
        } 
      />
      <Route 
        path="/tasks" 
        element={
          <PrivateRoute>
            <PrivateLayout>
              <div className="container">
                <h1>Tasks</h1>
                <TaskList />
              </div>
            </PrivateLayout>
          </PrivateRoute>
        } 
      />
      <Route 
        path="/people" 
        element={
          <PrivateRoute>
            <PrivateLayout>
              <div className="container">
                <h1>People</h1>
                <PeopleList />
              </div>
            </PrivateLayout>
          </PrivateRoute>
        } 
      />
      <Route 
        path="/create-task" 
        element={
          <PrivateRoute>
            <PrivateLayout>
              <div className="container">
                <h1>Create New Task</h1>
                <CreateTaskForm />
              </div>
            </PrivateLayout>
          </PrivateRoute>
        } 
      />
      <Route path="/" element={<Navigate to="/dashboard" />} />
      {/* <Route path="*" element={<div className="not-found">Page not found</div>} /> */}
    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app">
          <AppRoutes />
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;