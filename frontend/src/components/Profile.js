import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getUserProfile, updateUserProfile, fetchRoles } from '../api/userApi';
import { fetchTeams } from '../api/taskApi';

const UserProfile = () => {
  const { currentUser } = useAuth();
  const [userData, setUserData] = useState(null);
  const [teams, setTeams] = useState([]);
  const [roles, setRoles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  
  // Fetch user data, teams and roles
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        // Fetch user details
        const userData = await getUserProfile();
        setUserData(userData);
        
        // Fetch teams
        const teamsData = await fetchTeams();
        setTeams(teamsData);
        
        // Fetch roles
        const rolesData = await fetchRoles();
        setRoles(rolesData);
        console.log("debug roles: ", rolesData);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load user data. Please refresh and try again.');
        
        // Set current user as fallback if API fails
        if (currentUser) {
          setUserData(currentUser);
        }
        
        // Set default teams and roles if API fails
        setTeams([
          { id: '1', name: 'Development' },
          { id: '2', name: 'Design' },
          { id: '3', name: 'Marketing' }
        ]);
        
        setRoles([
          { id: '1', name: 'leader', permission_level: 3 },
          { id: '2', name: 'team_member', permission_level: 1 }
        ]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [currentUser]);
  
  useEffect(() => {
    if (userData) {
      console.log("debug user", userData);
    }
  }, [userData])

  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({
      ...userData,
      [name]: value
    });
  };

  const getPermissionLevel = (roleName) => {
    if (!roleName) return '?';
    if (roleName === 'team_member') return 1;
    if (roleName === 'manager') return 3;
    if (roleName === 'admin') return 4;
  } 
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // Only team_member role can't change role and team
      const isTeamMember = userData.role && userData.role === 'team_member';
      
      // If user is team_member, remove team and role from update data
      const updateUser = userData;
      
      setUserData({
        ...userData,
        ...updateUser
      });
      setIsEditing(false);
      
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update profile. Please try again.');
    }
  };
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading user profile...</p>
      </div>
    );
  }
  
  // Check if user exists
  if (!userData) {
    return (
      <div className="error-container">
        <div className="error-message">
          <h3>User data not available</h3>
          <p>There was a problem loading your profile information.</p>
          <button onClick={() => window.location.reload()} className="refresh-btn">
            Refresh
          </button>
        </div>
      </div>
    );
  }
  
  // Determine if user can edit role and team
  const canEditRoleAndTeam = userData.role && userData.role.permission_level > 1;
  
  return (
    <div className="container">
      <div className="user-profile-container">
        <div className="profile-header">
          <h2>User Profile</h2>
          {!isEditing && (
            <button className="edit-profile-btn" onClick={() => setIsEditing(true)}>
              <i className="fas fa-edit"></i> Edit Profile
            </button>
          )}
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="profile-content">
          {isEditing ? (
            <form className="profile-form" onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="first_name">First Name</label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={userData.first_name}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="last_name">Last Name</label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={userData.last_name}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={userData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="team">Team</label>
                  <select
                    id="team"
                    name="team"
                    value={userData.team}
                    onChange={handleChange}
                    disabled={!canEditRoleAndTeam}
                  >
                    <option value="">No Team</option>
                  </select>
                  {!canEditRoleAndTeam && (
                    <p className="field-note">Only managers can change team assignments</p>
                  )}
                </div>
                
                <div className="form-group">
                  <label htmlFor="role">Role</label>
                  <select
                    id="role"
                    name="role"
                    value={userData.role}
                    onChange={handleChange}
                    disabled={!canEditRoleAndTeam}
                  >
                    {roles.map(role => (
                      <option key={role.name} value={role.name}>
                        {role.name.charAt(0).toUpperCase() + role.name.slice(1)} (Level {role.permission_level})
                      </option>
                    ))}
                  </select>
                  {!canEditRoleAndTeam && (
                    <p className="field-note">Only managers can change roles</p>
                  )}
                </div>
              </div>
              
              <div className="form-actions">
                <button type="submit" className="save-btn">Save Changes</button>
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="profile-details">
              <div className="profile-avatar">
              {userData.profile_picture ? (
                <img src={userData.profile_picture} alt={`${userData.first_name} ${userData.last_name}`} className="user-avatar" />
              ) : (
                <div className="profile-avatar-placeholder">
                  {userData.username.charAt(0).toUpperCase()}
                </div>
              )}
              </div>
              
              <div className="profile-section">
                <h3>Personal Information</h3>
                <div className="detail-row">
                  <span className="detail-label">Name:</span>
                  <span className="detail-value">
                    {userData.first_name} {userData.last_name}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Username:</span>
                  <span className="detail-value">{userData.username}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Email:</span>
                  <span className="detail-value">{userData.email}</span>
                </div>
              </div>
              
              <div className="profile-section">
                <h3>Role and Team</h3>
                <div className="detail-row">
                  <span className="detail-label">Role:</span>
                  <span className="detail-value role-badge">
                    {userData.role ? userData.role.charAt(0).toUpperCase() + userData.role.slice(1) : 'Unknown'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Authority Level:</span>
                  <span className="detail-value">
                    Level {userData.role ? getPermissionLevel(userData.role) : 'Unknown'}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Team:</span>
                  <span className="detail-value team-badge">
                    {userData.team_name || 'No Team'}
                  </span>
                </div>
              </div>
              
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;