import React, { useState } from 'react';
import { fetchPersonDetails } from '../api/taskApi';

const PeopleList = ({ people }) => {
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Load person details when clicked
  const handlePersonClick = async (personId) => {
    // If clicking the same person, toggle the selection off
    if (selectedPerson && selectedPerson.id === personId) {
      setSelectedPerson(null);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const personDetails = await fetchPersonDetails(personId);
      setSelectedPerson(personDetails);
    } catch (err) {
      console.error('Error fetching person details:', err);
      setError('Failed to load person details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Generate a color based on name (for avatar)
  const generateAvatarColor = (name) => {
    if (!name) return '#6c757d';
    
    // Simple hash function to generate a color
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert to hex color
    let color = '#';
    for (let i = 0; i < 3; i++) {
      const value = (hash >> (i * 8)) & 0xFF;
      color += ('00' + value.toString(16)).substr(-2);
    }
    
    return color;
  };
  
  // Get initials from name
  const getInitials = (name) => {
    if (!name) return '?';
    
    const nameParts = name.split(' ');
    if (nameParts.length === 1) return nameParts[0].charAt(0).toUpperCase();
    
    return (nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)).toUpperCase();
  };
  
  // Render person card with initials avatar
  const renderPersonCard = (person) => {
    const isSelected = selectedPerson && selectedPerson.id === person.id;
    const avatarColor = generateAvatarColor(person.name);
    const initials = getInitials(person.name);
    
    return (
      <div 
        key={person.id}
        className={`person-card ${isSelected ? 'selected' : ''}`}
        onClick={() => handlePersonClick(person.id)}
      >
        <div 
          className="person-avatar" 
          style={{ backgroundColor: avatarColor }}
        >
          {person.profilePicture ? (
            <img src={person.profilePicture} alt={person.name} />
          ) : (
            <span className="person-initials">{initials}</span>
          )}
        </div>
        
        <div className="person-info">
          <h4 className="person-name">{person.name}</h4>
          {person.role && <p className="person-role">{person.role}</p>}
        </div>
      </div>
    );
  };
  
  // Render person details when selected
  const renderPersonDetails = () => {
    if (!selectedPerson) return null;
    
    return (
      <div className="person-details-panel">
        <div className="person-details-header">
          <h3>{selectedPerson.name}</h3>
          <button 
            className="close-details-btn"
            onClick={() => setSelectedPerson(null)}
          >
            ×
          </button>
        </div>
        
        <div className="person-details-content">
          {selectedPerson.role && (
            <div className="detail-item">
              <span className="detail-label">Role:</span>
              <span className="detail-value">{selectedPerson.role}</span>
            </div>
          )}
          
          {selectedPerson.email && (
            <div className="detail-item">
              <span className="detail-label">Email:</span>
              <span className="detail-value">{selectedPerson.email}</span>
            </div>
          )}
          
          {selectedPerson.phone && (
            <div className="detail-item">
              <span className="detail-label">Phone:</span>
              <span className="detail-value">{selectedPerson.phone}</span>
            </div>
          )}
          
          {selectedPerson.teams && selectedPerson.teams.length > 0 && (
            <div className="detail-item">
              <span className="detail-label">Teams:</span>
              <div className="detail-value teams-list">
                {selectedPerson.teams.map(team => (
                  <span key={team._id} className="team-tag">
                    {team.name}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {selectedPerson.skills && selectedPerson.skills.length > 0 && (
            <div className="detail-item">
              <span className="detail-label">Skills:</span>
              <div className="detail-value skills-list">
                {selectedPerson.skills.map((skill, index) => (
                  <span key={index} className="skill-tag">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {selectedPerson.taskHistory && selectedPerson.taskHistory.length > 0 && (
          <div className="person-task-history">
            <h4>Recent Tasks</h4>
            <ul className="history-list">
              {selectedPerson.taskHistory.slice(0, 5).map((task, index) => (
                <li key={index} className="history-item">
                  <span className="task-title">{task.title}</span>
                  <span className="task-status">{task.status}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="person-details-actions">
          <button className="action-btn assign-task">
            Assign Task
          </button>
          <button className="action-btn view-all-tasks">
            View All Tasks
          </button>
        </div>
      </div>
    );
  };
  
  // Empty state if no people
  if (!people || people.length === 0) {
    return (
      <div className="empty-people-list">
        <p>No people available.</p>
      </div>
    );
  }
  
  return (
    <div className="people-list-container">
      {error && <div className="error-message">{error}</div>}
      
      <div className="people-grid">
        {people.map(renderPersonCard)}
      </div>
      
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading person details...</p>
        </div>
      )}
      
      {renderPersonDetails()}
    </div>
  );
};

export default PeopleList;
