import React, { useState } from 'react';
import { updateTask, deleteTask } from '../api/taskApi';

const TaskList = ({ tasks }) => {
  const [expandedTaskId, setExpandedTaskId] = useState(null);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // Toggle task details expanded/collapsed
  const toggleTaskDetails = (taskId) => {
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
  };

  // Start editing a task
  const startEditing = (task) => {
    setEditingTaskId(task.id);
    setEditFormData({ ...task });
  };

  // Cancel editing
  const cancelEditing = () => {
    setEditingTaskId(null);
    setEditFormData({});
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditFormData({
      ...editFormData,
      [name]: value
    });
  };

  // Save edited task
  const saveTask = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    
    try {
      await updateTask(editingTaskId, editFormData);
      setSuccessMessage('Task updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      setEditingTaskId(null);
      
      // Refresh tasks (handled by parent component ideally)
      // This is a simplified approach - in a real app you'd use context or redux
      window.location.reload();
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete a task
  const removeTask = async (taskId) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }
    
    try {
      await deleteTask(taskId);
      setSuccessMessage('Task deleted successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      
      // Refresh tasks (handled by parent component ideally)
      window.location.reload();
    } catch (err) {
      console.error('Error deleting task:', err);
      setError('Failed to delete task');
    }
  };

  // Get CSS class based on task priority
  const getPriorityClass = (priority) => {
    const priorityMap = {
      'low': 'priority-low',
      'medium': 'priority-medium',
      'high': 'priority-high',
      'urgent': 'priority-urgent'
    };
    return priorityMap[priority] || 'priority-medium';
  };

  // Get CSS class based on task status
  const getStatusClass = (status) => {
    const statusMap = {
      'todo': 'status-todo',
      'in_progress': 'status-in-progress',
      'review': 'status-review',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled'
    };
    return statusMap[status] || 'status-todo';
  };

  // Format date string for display
  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  // Check if a task is past due
  const isPastDue = (dueDate) => {
    if (!dueDate) return false;
    const now = new Date();
    const due = new Date(dueDate);
    return due < now;
  };

  // Render a single task item
  const renderTaskItem = (task) => {
    const isExpanded = expandedTaskId === task.id;
    const isEditing = editingTaskId === task.id;
    const isOverdue = isPastDue(task.dueDate);
    
    return (
      <div 
        key={task.id} 
        className={`task-item ${isExpanded ? 'expanded' : ''} ${isOverdue ? 'overdue' : ''}`}
      >
        {/* Task summary (always visible) */}
        <div className="task-summary" onClick={() => toggleTaskDetails(task.id)}>
          <div className="task-title-section">
            <h4 className="task-title">{task.title}</h4>
            <div className="task-badges">
              <span className={`task-priority ${getPriorityClass(task.priority)}`}>
                {task.priority}
              </span>
              <span className={`task-status ${getStatusClass(task.status)}`}>
                {task.status}
              </span>
            </div>
          </div>
          <div className="task-meta">
            {task.dueDate && (
              <span className={`task-due-date ${isOverdue ? 'overdue' : ''}`}>
                Due: {formatDate(task.dueDate)}
              </span>
            )}
            <button className="task-expand-btn">
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
          </div>
        </div>
        
        {/* Task details (visible when expanded) */}
        {isExpanded && !isEditing && (
          <div className="task-details">
            <p className="task-description">{task.description}</p>
            <div className="task-attributes">
              <div className="task-attribute">
                <strong>Assigned to:</strong> 
                <span>{task.assignedTo_details?.first_name} {task.assignedTo_details?.last_name}</span>
              </div>
              <div className="task-attribute">
                <strong>Created by:</strong> 
                <span>{task.assigned_by_details?.first_name} {task.assigned_by_details?.last_name}</span>
              </div>
              {task.team && (
                <div className="task-attribute">
                  <strong>Team:</strong> <span>{task.team_details?.name}</span>
                </div>
              )}
              {task.aiGenerated && (
                <div className="task-attribute ai-generated">
                  <strong>AI Generated</strong> 
                  {task.aiConfidenceScore && (
                    <span>Confidence: {Math.round(task.aiConfidenceScore * 100)}%</span>
                  )}
                </div>
              )}
            </div>
            <div className="task-actions">
              <button 
                className="edit-task-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  startEditing(task);
                }}
              >
                Edit
              </button>
              <button 
                className="delete-task-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  removeTask(task.id);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        )}
        
        {/* Edit form (visible when editing) */}
        {isEditing && (
          <div className="task-edit-form">
            <form onSubmit={saveTask}>
              <div className="form-group">
                <label htmlFor="title">Title</label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={editFormData.title || ''}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={editFormData.description || ''}
                  onChange={handleInputChange}
                  rows="3"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="status">Status</label>
                  <select
                    id="status"
                    name="status"
                    value={editFormData.status || ''}
                    onChange={handleInputChange}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="review">Review</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label htmlFor="priority">Priority</label>
                  <select
                    id="priority"
                    name="priority"
                    value={editFormData.priority || ''}
                    onChange={handleInputChange}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="dueDate">Due Date</label>
                <input
                  type="date"
                  id="dueDate"
                  name="dueDate"
                  value={editFormData.dueDate ? new Date(editFormData.dueDate).toISOString().split('T')[0] : ''}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="form-actions">
                <button 
                  type="submit" 
                  className="save-task-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={cancelEditing}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    );
  };

  // Empty state if no tasks
  if (!tasks || tasks.length === 0) {
    return (
      <div className="empty-task-list">
        <p>No tasks available. Create a new task to get started.</p>
      </div>
    );
  }

  return (
    <div className="task-list">
      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}
      
      {tasks.map(renderTaskItem)}
    </div>
  );
};

export default TaskList;