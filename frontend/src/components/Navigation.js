import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navigation = () => {
  const { currentUser, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // If user is not logged in, don't show navigation
  if (!currentUser) return null;

  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
    if (userMenuOpen) setUserMenuOpen(false);
  };

  // Toggle user menu
  const toggleUserMenu = () => {
    setUserMenuOpen(!userMenuOpen);
    if (mobileMenuOpen) setMobileMenuOpen(false);
  };

  // Handle logout
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Check if the given path matches the current location
  const isActive = (path) => {
    return location.pathname === path;
  };

  // Get initials from name
  const getInitials = (name) => {
    if (!name) return '?';
    
    const nameParts = name.split(' ');
    if (nameParts.length === 1) return nameParts[0].charAt(0).toUpperCase();
    
    return (nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)).toUpperCase();
  };

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        <div className="nav-logo">
          <Link to="/dashboard">
            <span className="logo-text">TaskMaster</span>
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <button 
          className="mobile-menu-toggle"
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          <span className="menu-icon"></span>
        </button>

        {/* Main navigation links */}
        <div className={`nav-links ${mobileMenuOpen ? 'active' : ''}`}>
          <Link 
            to="/dashboard" 
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
          >
            <i className="fas fa-tachometer-alt nav-icon"></i>
            <span>Dashboard</span>
          </Link>
          
          <Link 
            to="/tasks" 
            className={`nav-link ${isActive('/tasks') ? 'active' : ''}`}
          >
            <i className="fas fa-tasks nav-icon"></i>
            <span>Tasks</span>
          </Link>
          
          <Link 
            to="/people" 
            className={`nav-link ${isActive('/people') ? 'active' : ''}`}
          >
            <i className="fas fa-users nav-icon"></i>
            <span>People</span>
          </Link>
          
          <Link 
            to="/create-task" 
            className={`nav-link ${isActive('/create-task') ? 'active' : ''}`}
          >
            <i className="fas fa-plus-circle nav-icon"></i>
            <span>New Task</span>
          </Link>
          
          {currentUser.role === 'leader' && (
            <Link 
              to="/reports" 
              className={`nav-link ${isActive('/reports') ? 'active' : ''}`}
            >
              <i className="fas fa-chart-bar nav-icon"></i>
              <span>Reports</span>
            </Link>
          )}
        </div>

        {/* User menu */}
        <div className="user-menu-container">
          <button 
            className="user-menu-toggle"
            onClick={toggleUserMenu}
            aria-label="User menu"
          >
            {currentUser.profilePicture ? (
              <img 
                src={currentUser.profilePicture} 
                alt={currentUser.name || currentUser.username} 
                className="user-avatar"
              />
            ) : (
              <div className="user-avatar-placeholder">
                {getInitials(currentUser.name || currentUser.username)}
              </div>
            )}
            <span className="user-name">{currentUser.name || currentUser.username}</span>
            <i className={`fas fa-chevron-${userMenuOpen ? 'up' : 'down'} user-menu-arrow`}></i>
          </button>
          
          {userMenuOpen && (
            <div className="user-dropdown-menu">
              <div className="user-info">
                <div className="user-info-name">{currentUser.name || currentUser.username}</div>
                <div className="user-info-email">{currentUser.email}</div>
                <div className="user-info-role">{currentUser.role}</div>
              </div>
              
              <Link to="/profile" className="dropdown-item">
                <i className="fas fa-user-circle dropdown-icon"></i>
                Profile
              </Link>
              
              <Link to="/settings" className="dropdown-item">
                <i className="fas fa-cog dropdown-icon"></i>
                Settings
              </Link>
              
              <button onClick={handleLogout} className="dropdown-item logout-button">
                <i className="fas fa-sign-out-alt dropdown-icon"></i>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;