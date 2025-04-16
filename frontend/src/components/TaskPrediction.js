import React, { useState } from 'react';
import { getPredictedTasks } from '../api/aiApi';
import { createTask } from '../api/taskApi';

const TaskPrediction = ({ people }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [predictions, setPredictions] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Generate task predictions for a specific person
  const generatePredictions = async () => {
    if (!selectedPerson) {
      setError('Please select a person first');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await getPredictedTasks(selectedPerson);
      setPredictions(result.predictedTasks || []);
      
      if (!(result.predictedTasks && result.predictedTasks.length > 0)) {
        setError('No predictions could be generated at this time');
      }
    } catch (err) {
      console.error('Error generating predictions:', err);
      setError('Failed to generate predictions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Save a predicted task to the database
  const savePredictedTask = async (task) => {
    try {
      await createTask({
        ...task,
        status: 'todo',
        aiGenerated: true
      });
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
      
      // Remove the saved task from predictions
      setPredictions(predictions.filter(p => p !== task));
    } catch (err) {
      console.error('Error saving predicted task:', err);
      setError('Failed to save task. Please try again.');
    }
  };

  return (
    <div className="task-prediction-container">
      <h3>AI Task Predictions</h3>
      <p className="prediction-description">
        Generate AI-powered predictions for upcoming tasks based on task history and patterns.
      </p>

      <div className="prediction-controls">
        <div className="person-selector">
          <label htmlFor="person-select">Select person:</label>
          <select 
            id="person-select"
            value={selectedPerson}
            onChange={(e) => setSelectedPerson(e.target.value)}
            disabled={isLoading}
          >
            <option value="">Choose a person</option>
            {people.map(person => (
              <option key={person.id} value={person.id}>
                {person.name}
              </option>
            ))}
          </select>
        </div>

        <button 
          className="generate-predictions-btn"
          onClick={generatePredictions}
          disabled={isLoading || !selectedPerson}
        >
          {isLoading ? 'Generating...' : 'Generate Predictions'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      
      {showSuccess && (
        <div className="success-message">Task saved successfully!</div>
      )}

      {predictions.length > 0 && (
        <div className="predictions-list">
          <h4>Predicted Tasks</h4>
          {predictions.map((prediction, index) => (
            <div key={index} className="prediction-card">
              <div className="prediction-header">
                <h5>{prediction.title}</h5>
                <span className={`confidence-badge confidence-${Math.floor(prediction.confidence * 10)}`}>
                  {Math.round(prediction.confidence * 100)}%
                </span>
              </div>
              <p className="prediction-description">{prediction.description}</p>
              <div className="prediction-meta">
                {prediction.dueDate && (
                  <span className="prediction-due-date">
                    <i className="far fa-calendar"></i> Due: {prediction.dueDate}
                  </span>
                )}
                <span className={`prediction-priority priority-${prediction.priority}`}>
                  {prediction.priority}
                </span>
              </div>
              <div className="prediction-actions">
                <button 
                  className="save-prediction-btn"
                  onClick={() => savePredictedTask(prediction)}
                >
                  Create Task
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TaskPrediction;