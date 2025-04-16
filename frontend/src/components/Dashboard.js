import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchTasks, fetchPeople } from '../api/taskApi';
import TaskList from './TaskList';
import PeopleList from './PeopleList';
import AudioRecorder from './AudioRecorder';
import TaskPrediction from './TaskPrediction';
import Statistics from './Statistics';
import CreateTaskForm from './CreateTaskForm';

const Dashboard = () => {
  const [tasks, setTasks] = useState([]);
  const [people, setPeople] = useState([]);
  const [teams, setTeams] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { currentUser } = useAuth();
  
  // Determine if user is a leader or team member
  const isLeader = currentUser?.role === 'leader';

  // Fetch teams data
  const fetchTeams = async () => {
    try {
      // This would be your actual API call
      const response = await fetch('/api/teams', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch teams');
      }
      
      const data = await response.json();
      setTeams(data);
    } catch (err) {
      console.error('Error fetching teams:', err);
      // Set default teams for demo purposes
      setTeams([
        { id: '1', name: 'Development' },
        { id: '2', name: 'Design' },
        { id: '3', name: 'Marketing' }
      ]);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Fetch tasks relevant to the user's role
        const tasksData = await fetchTasks(currentUser.id, currentUser.role);
        setTasks(tasksData);
        
        // Leaders see all people, team members see only themselves and direct collaborators
        const peopleData = await fetchPeople(currentUser.id, currentUser.role);
        setPeople(peopleData);
        
        // Fetch teams
        await fetchTeams();
      } catch (err) {
        console.error("Error loading dashboard data:", err);
        setError("Failed to load dashboard data. Please refresh and try again.");
        
        // Set default data for demo purposes
        setTasks([]);
        setPeople([
          { id: '1', name: 'John Doe', role: 'Developer' },
          { id: '2', name: 'Jane Smith', role: 'Designer' }
        ]);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (currentUser) {
      loadData();
    }
  }, [currentUser]);

  // Refresh tasks after a new task is created
  const refreshTasks = async () => {
    try {
      const tasksData = await fetchTasks(currentUser.id, currentUser.role);
      setTasks(tasksData);
    } catch (err) {
      console.error("Error refreshing tasks:", err);
    }
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error-message">{error}</div>
        <button onClick={() => window.location.reload()} className="refresh-btn">
          Refresh
        </button>
      </div>
    );
  }

  // Render different components based on user role
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Welcome, {currentUser?.name || currentUser?.username}</h1>
        <p>Role: {currentUser?.role}</p>
      </header>
      
      <div className="dashboard-content">
        {/* Main task area */}
        <div className="dashboard-main">
          {/* Quick task creation */}
          <section className="dashboard-section quick-create-section">
            <h2>Quick Task Creation</h2>
            <CreateTaskForm 
              people={people} 
              teams={teams} 
              onTaskCreated={refreshTasks}
            />
          </section>
          
          {/* My tasks */}
          <section className="dashboard-section tasks-section">
            <h2>My Tasks</h2>
            <TaskList 
              tasks={tasks.filter(task => task.assignedTo === currentUser.id)} 
            />
          </section>
        </div>
        
        {/* Sidebar */}
        <div className="dashboard-sidebar">
          {/* Role-specific components */}
          {isLeader ? (
            <>
              {/* Team overview for leaders */}
              <section className="dashboard-section team-section">
                <h2>Team Overview</h2>
                <PeopleList people={people} />
                <Statistics peopleData={people} tasksData={tasks} />
              </section>
              
              {/* AI tools for leaders */}
              <section className="dashboard-section ai-tools">
                <h2>AI Task Management</h2>
                <div className="ai-tools-tabs">
                  <div className="tab-header">
                    <button className="tab-button active">Predictions</button>
                    <button className="tab-button">Voice Recording</button>
                  </div>
                  <div className="tab-content">
                    <TaskPrediction people={people} />
                  </div>
                </div>
              </section>
            </>
          ) : (
            <>
              {/* Collaborators for team members */}
              <section className="dashboard-section collaborators-section">
                <h2>My Collaborators</h2>
                <PeopleList people={people} />
              </section>
              
              {/* Quick voice recording for team members */}
              <section className="dashboard-section recording-section">
                <h2>Voice Task Recording</h2>
                <AudioRecorder userId={currentUser.id} />
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;