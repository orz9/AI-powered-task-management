# AI-Assisted People-First Task Management System

A modern, AI-powered task management system that focuses on people first, dynamically creating and managing tasks based on individuals' roles, responsibilities, and past activities.

## Features

- **Role-based Dynamic UI**: Different dashboards and controls for leaders vs. team members
- **AI-powered Task Predictions**: Uses OpenAI's GPT to predict upcoming tasks based on historical data and context
- **Speech-to-Text Integration**: OpenAI Whisper API integration for converting audio inputs into actionable tasks
- **People-Centric Design**: Emphasizes managing people first, with tasks organized around them
- **Modern, Responsive UI**: Clean, intuitive interface that works across devices

## Technology Stack

### Backend
- **Framework**: Django with Django REST Framework
- **Database**: MongoDB (with Mongoose schemas)
- **AI Integration**: OpenAI GPT and Whisper APIs
- **Authentication**: JWT-based authentication

### Frontend
- **Framework**: React.js
- **State Management**: React Context API
- **UI Components**: Custom components with modern CSS
- **API Integration**: Axios for API requests

## Project Structure

```
/
├── backend/                  # Django backend application
│   ├── ai_integration/       # AI integration services
│   ├── people/               # People and users management
│   └── tasks/                # Task management
├── frontend/                 # React frontend application
│   ├── public/               # Public assets
│   └── src/                  # React source code
│       ├── api/              # API integration
│       ├── components/       # React components
│       ├── context/          # Context providers
│       └── styles/           # CSS styles
└── README.md                 # Project documentation
```

## Installation

### Prerequisites
- Node.js (v14+)
- Python (v3.8+)
- MongoDB

### Backend Setup
1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in a .env file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   MONGODB_URI=your_mongodb_connection_string
   SECRET_KEY=your_django_secret_key
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the server:
   ```
   python manage.py runserver
   ```

### Frontend Setup
1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Create .env file with backend API URL:
   ```
   REACT_APP_API_BASE_URL=http://localhost:8000/api
   ```

3. Start the development server:
   ```
   npm start
   ```

## AI Integration

### OpenAI API Integration
The system uses two primary OpenAI APIs:

1. **GPT for Task Prediction**:
   - Analyzes patterns in completed tasks
   - Considers user role, responsibilities, and work history
   - Predicts upcoming tasks with confidence scores

2. **Whisper for Speech-to-Text**:
   - Transcribes spoken meeting notes or task descriptions
   - Processes transcription to extract actionable tasks
   - Handles assignments, due dates, and priorities

### Error Handling
The system implements robust error handling for AI integration:
- Rate limiting and retry mechanisms
- Confidence scoring for transcriptions and predictions
- Fallback mechanisms when AI services are unavailable

## Database Schema

The MongoDB schema is designed for flexibility and performance:

- **User Schema**: Authentication and user preferences
- **Person Schema**: Representing individuals with skills and relationships
- **Task Schema**: Comprehensive task data with history tracking
- **Team Schema**: Team structures and relationships
- **Project Schema**: Project management
- **AI Training Data Schema**: Storing data to improve AI predictions

## API Endpoints

### Authentication
- `POST /api/auth/login/`: User login
- `POST /api/auth/register/`: User registration
- `GET /api/auth/user/`: Get current user

### Tasks
- `GET /api/tasks/`: List all tasks
- `POST /api/tasks/`: Create new task
- `GET /api/tasks/{id}/`: Get task details
- `PUT /api/tasks/{id}/`: Update task
- `DELETE /api/tasks/{id}/`: Delete task

### People
- `GET /api/people/`: List all people
- `GET /api/people/{id}/`: Get person details
- `GET /api/people/related/{id}/`: Get people related to a user

### AI Integration
- `POST /api/ai/process-audio/`: Process audio for transcription and task extraction
- `POST /api/ai/predict-tasks/`: Generate task predictions
- `GET /api/ai/analyze-tasks/{id}/`: Get task analysis and insights

## User Roles and Permissions

- **Team Member**:
  - Manage own tasks
  - View assigned tasks
  - Record tasks via voice
  - See collaborators

- **Team Leader**:
  - View team performance
  - Assign tasks to team members
  - Access AI predictions for team
  - Generate insights and reports

- **Admin**:
  - Manage all users and teams
  - Configure system settings
  - Access all data

## License

MIT License
