import React, { useState, useEffect } from 'react';
import { fetchTasks, updateTask, deleteTask } from '../api/taskApi';
import { useAuth } from '../context/AuthContext';

const TaskList = ({ tasks: initialTasks }) => {
  const { currentUser } = useAuth();
  const [tasks, setTasks] = useState(initialTasks || []);
  const [expandedTaskId, setExpandedTaskId] = useState(null);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(!initialTasks);

  // Fetch tasks if they were not provided as props
  useEffect(() => {
    if (initialTasks) {
      setTasks(initialTasks);
      return;
    }
    
    const loadTasks = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Log user information for debugging
        console.log("Current user:", currentUser);
        
        const tasksData = await fetchTasks(currentUser?.id, currentUser?.role);
        console.log("Fetched tasks:", tasksData); // Debug log
        setTasks(tasksData);
      } catch (err) {
        console.error("Error loading tasks:", err);
        setError("Failed to load tasks. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };
    
    if (currentUser) {
      loadTasks();
    }
  }, [initialTasks, currentUser]);

  // Toggle task details expanded/collapsed
  const toggleTaskDetails = (taskId) => {
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
  };

  // Start editing a task
  const startEditing = (task) => {
    // Log the task to see its structure
    console.log("Editing task:", task);
    
    // Ensure we have the correct ID format
    const taskId = task._id || task.id;
    
    // Normalize the date format for the form
    let dueDateFormatted = "";
    if (task.dueDate || task.due_date) {
      const dueDate = new Date(task.dueDate || task.due_date);
      if (!isNaN(dueDate.getTime())) {
        dueDateFormatted = dueDate.toISOString().split('T')[0];
      }
    }
    
    // Normalize field names to ensure form has the right fields
    const normalizedTask = {
      id: taskId,
      title: task.title || "",
      description: task.description || "",
      status: task.status || "todo",
      priority: task.priority || "medium",
      dueDate: dueDateFormatted
    };
    
    setEditingTaskId(taskId);
    setEditFormData(normalizedTask);
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
      console.log("Saving task with ID:", editingTaskId);
      console.log("Form data:", editFormData);
      
      // Format the data for the API
      const updateData = {
        title: editFormData.title,
        description: editFormData.description,
        status: editFormData.status,
        priority: editFormData.priority,
        dueDate: editFormData.dueDate || null
      };
      
      const updatedTask = await updateTask(editingTaskId, updateData);
      console.log("Updated task:", updatedTask);
      
      // Update the task in the local state
      setTasks(tasks.map(task => 
        (task._id === editingTaskId || task.id === editingTaskId) ? updatedTask : task
      ));
      
      setSuccessMessage('Task updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      setEditingTaskId(null);
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task. Please try again.');
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
      console.log("Deleting task with ID:", taskId);
      await deleteTask(taskId);
      
      // Remove the task from local state
      setTasks(tasks.filter(task => task._id !== taskId && task.id !== taskId));
      
      setSuccessMessage('Task deleted successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Error deleting task:', err);
      setError('Failed to delete task. Please try again.');
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
      'done': 'status-completed',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled'
    };
    return statusMap[status] || 'status-todo';
  };

  // Format date string for display
  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid date';
    return date.toLocaleDateString();
  };

  // Check if a task is past due
  const isPastDue = (dueDate) => {
    if (!dueDate) return false;
    const now = new Date();
    const due = new Date(dueDate);
    if (isNaN(due.getTime())) return false;
    return due < now;
  };

  // Helper to get assigned person name
  const getAssigneeName = (task) => {
    // Debug log to see what's available
    console.log("Assignee info:", {
      assigned_to: task.assigned_to,
      assigned_to_details: task.assigned_to_details
    });
    
    if (task.assigned_to_details?.name) {
      return task.assigned_to_details.name;
    }
    
    return 'Not assigned';
  };
  
  // Helper to get creator name
  const getCreatorName = (task) => {
    // Debug log to see what's available
    console.log("Creator info:", {
      assigned_by: task.assigned_by,
      assigned_by_details: task.assigned_by_details
    });
    
    if (task.assigned_by_details?.name) {
      return task.assigned_by_details.name;
    }
    
    return 'Unknown';
  };
  
  // Helper to get team name
  const getTeamName = (task) => {
    if (task.team_details?.name) {
      return task.team_details.name;
    }
    
    return 'No team';
  };

  // Render a single task item
  const renderTaskItem = (task) => {
    // Use _id from MongoDB (consistent with backend)
    const taskId = task._id || task.id;
    const isExpanded = expandedTaskId === taskId;
    const isEditing = editingTaskId === taskId;
    const isOverdue = isPastDue(task.dueDate || task.due_date);
    
    return (
      <div 
        key={taskId} 
        className={`task-item ${isExpanded ? 'expanded' : ''} ${isOverdue ? 'overdue' : ''}`}
      >
        {/* Task summary (always visible) */}
        <div className="task-summary" onClick={() => toggleTaskDetails(taskId)}>
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
            {(task.dueDate || task.due_date) && (
              <span className={`task-due-date ${isOverdue ? 'overdue' : ''}`}>
                Due: {formatDate(task.dueDate || task.due_date)}
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
                <span>{getAssigneeName(task)}</span>
              </div>
              <div className="task-attribute">
                <strong>Created by:</strong> 
                <span>{getCreatorName(task)}</span>
              </div>
              <div className="task-attribute">
                <strong>Team:</strong> 
                <span>{getTeamName(task)}</span>
              </div>
              {(task.aiGenerated || task.ai_generated) && (
                <div className="task-attribute ai-generated">
                  <strong>AI Generated</strong>
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
                  removeTask(taskId);
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
                    <option value="done">Done</option>
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
                  value={editFormData.dueDate || ''}
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

  // Show loading state
  if (isLoading) {
    return (
      <div className="loading-tasks">
        <div className="loading-spinner"></div>
        <p>Loading tasks...</p>
      </div>
    );
  }

  // Show error state
  if (error && !tasks.length) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
        <button onClick={() => window.location.reload()} className="refresh-btn">
          Refresh
        </button>
      </div>
    );
  }

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