import React, { useEffect, useState } from 'react';
import { getTaskAnalysis } from '../api/aiApi';

const Statistics = ({ peopleData, tasksData }) => {
  const [timeframe, setTimeframe] = useState('month');
  const [insights, setInsights] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    inProgress: 0,
    overdue: 0,
    completionRate: 0,
    aiGenerated: 0
  });

  // Calculate basic statistics from tasks data
  useEffect(() => {
    if (!tasksData || tasksData.length === 0) return;

    const now = new Date();
    const total = tasksData.length;
    const completed = tasksData.filter(task => task.status === 'done').length;
    const inProgress = tasksData.filter(task => task.status === 'in_progress').length;
    const overdue = tasksData.filter(task => {
      if (!task.dueDate) return false;
      const dueDate = new Date(task.dueDate);
      return dueDate < now && task.status !== 'done';
    }).length;
    const aiGenerated = tasksData.filter(task => task.aiGenerated).length;
    
    setStats({
      total,
      completed,
      inProgress,
      overdue,
      completionRate: total > 0 ? Math.round((completed / total) * 100) : 0,
      aiGenerated
    });
  }, [tasksData]);

  // Load AI insights for tasks
  const loadInsights = async () => {
    if (!peopleData || peopleData.length === 0) return;
    
    // For this example, we'll just use the first person's ID
    // In a real application, you might want to allow selecting a person
    const personId = peopleData[0].id;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await getTaskAnalysis(personId, timeframe);
      setInsights(result.insights || []);
    } catch (err) {
      console.error('Error loading insights:', err);
      setError('Failed to load AI insights');
    } finally {
      setIsLoading(false);
    }
  };

  // Load insights when timeframe changes
  useEffect(() => {
    loadInsights();
  }, [timeframe, peopleData]);

  // Format insight confidence as percentage
  const formatConfidence = (confidence) => {
    if (confidence === undefined || confidence === null) return '';
    return `${Math.round(confidence * 100)}%`;
  };

  return (
    <div className="statistics-container">
      <div className="statistics-header">
        <h3>Team Statistics</h3>
        <div className="timeframe-selector">
          <label htmlFor="timeframe-select">Time period:</label>
          <select
            id="timeframe-select"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            disabled={isLoading}
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
            <option value="year">Last Year</option>
          </select>
        </div>
      </div>

      {/* Task metrics cards */}
      <div className="metrics-cards">
        <div className="metric-card">
          <div className="metric-icon total-icon">
            <i className="fas fa-tasks"></i>
          </div>
          <div className="metric-content">
            <h4 className="metric-value">{stats.total}</h4>
            <p className="metric-label">Total Tasks</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon completed-icon">
            <i className="fas fa-check-circle"></i>
          </div>
          <div className="metric-content">
            <h4 className="metric-value">{stats.completed}</h4>
            <p className="metric-label">Completed</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon progress-icon">
            <i className="fas fa-spinner"></i>
          </div>
          <div className="metric-content">
            <h4 className="metric-value">{stats.inProgress}</h4>
            <p className="metric-label">In Progress</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon overdue-icon">
            <i className="fas fa-exclamation-circle"></i>
          </div>
          <div className="metric-content">
            <h4 className="metric-value">{stats.overdue}</h4>
            <p className="metric-label">Overdue</p>
          </div>
        </div>
      </div>

      {/* Performance indicators */}
      <div className="performance-indicators">
        <div className="indicator">
          <span className="indicator-label">Completion Rate:</span>
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${stats.completionRate}%` }}
            ></div>
            <span className="progress-value">{stats.completionRate}%</span>
          </div>
        </div>

        <div className="indicator">
          <span className="indicator-label">AI Generated Tasks:</span>
          <span className="indicator-value">{stats.aiGenerated}</span>
        </div>
      </div>

      {/* AI Insights section */}
      <div className="ai-insights-section">
        <h4>AI Insights</h4>
        
        {isLoading && (
          <div className="loading-message">Loading insights...</div>
        )}
        
        {error && (
          <div className="error-message">{error}</div>
        )}
        
        {insights.length === 0 && !isLoading && !error && (
          <div className="no-insights-message">
            No insights available for the selected timeframe.
          </div>
        )}
        
        {insights.length > 0 && (
          <div className="insights-list">
            {insights.map((insight, index) => (
              <div key={index} className="insight-card">
                <div className="insight-header">
                  <h5 className="insight-title">{insight.title || 'Insight'}</h5>
                  <span className="insight-confidence">
                    {formatConfidence(insight.confidence)}
                  </span>
                </div>
                <p className="insight-description">{insight.description}</p>
                {insight.recommendation && (
                  <div className="insight-recommendation">
                    <strong>Recommendation:</strong> {insight.recommendation}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Statistics;