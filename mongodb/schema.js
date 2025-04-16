// User Schema
const UserSchema = {
    _id: ObjectId,
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true }, // Hashed password
    name: { type: String, required: true },
    role: { 
      type: String, 
      enum: ['leader', 'team_member', 'admin'], 
      default: 'team_member' 
    },
    organization: { type: ObjectId, ref: 'Organization' },
    teams: [{ type: ObjectId, ref: 'Team' }],
    preferences: {
      theme: { type: String, default: 'light' },
      notificationSettings: {
        email: { type: Boolean, default: true },
        inApp: { type: Boolean, default: true },
      },
      dashboardLayout: { type: Object }
    },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now },
    lastLogin: { type: Date }
  }
  
  // Create index for faster queries
  db.users.createIndex({ email: 1 }); // Unique index for email
  db.users.createIndex({ organization: 1 }); // Index for organization lookup
  db.users.createIndex({ teams: 1 }); // Index for team lookup
  
  // Person Schema (representing individuals in the system)
  const PersonSchema = {
    _id: ObjectId,
    userId: { type: ObjectId, ref: 'User', required: false }, // If the person has a system account
    name: { type: String, required: true },
    email: { type: String, required: false },
    phone: { type: String, required: false },
    role: { type: String, required: false },
    organization: { type: ObjectId, ref: 'Organization', required: true },
    teams: [{ type: ObjectId, ref: 'Team' }],
    skills: [String],
    relationships: [{
      personId: { type: ObjectId, ref: 'Person' },
      relationshipType: { 
        type: String, 
        enum: ['manager', 'direct_report', 'peer', 'collaborator'] 
      }
    }],
    taskHistory: [{
      taskId: { type: ObjectId, ref: 'Task' },
      role: { type: String, enum: ['assignee', 'creator', 'reviewer'] },
      completedAt: { type: Date }
    }],
    tags: [String], // For classification and filtering
    metadata: { type: Object }, // Flexible field for additional data
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for Person collection
  db.people.createIndex({ userId: 1 }); // Link to user account
  db.people.createIndex({ organization: 1 }); // Filter by organization
  db.people.createIndex({ teams: 1 }); // Filter by team
  db.people.createIndex({ "relationships.personId": 1 }); // Query relationships
  db.people.createIndex({ tags: 1 }); // Search by tags
  
  // Task Schema
  const TaskSchema = {
    _id: ObjectId,
    title: { type: String, required: true },
    description: { type: String, required: false },
    status: { 
      type: String, 
      enum: ['pending', 'in_progress', 'review', 'completed', 'cancelled'], 
      default: 'pending' 
    },
    priority: { 
      type: String, 
      enum: ['low', 'medium', 'high', 'urgent'], 
      default: 'medium' 
    },
    assignedTo: { type: ObjectId, ref: 'Person', required: true },
    createdBy: { type: ObjectId, ref: 'Person', required: true },
    relatedPeople: [{ 
      personId: { type: ObjectId, ref: 'Person' },
      role: { type: String } // Collaborator, reviewer, etc.
    }],
    dueDate: { type: Date, required: false },
    completedAt: { type: Date, required: false },
    project: { type: ObjectId, ref: 'Project', required: false },
    team: { type: ObjectId, ref: 'Team', required: false },
    organization: { type: ObjectId, ref: 'Organization', required: true },
    tags: [String],
    aiGenerated: { type: Boolean, default: false }, // Flag if task was AI-generated
    aiConfidence: { type: Number, min: 0, max: 1 }, // Confidence score for AI-generated tasks
    source: { 
      type: String,
      enum: ['manual', 'transcription', 'prediction', 'imported'],
      default: 'manual'
    },
    sourceData: { type: Object }, // Additional data about task source
    attachments: [{
      name: { type: String },
      fileUrl: { type: String },
      fileType: { type: String },
      uploadedAt: { type: Date, default: Date.now }
    }],
    history: [{
      field: { type: String }, // Field that changed
      oldValue: { type: mongoose.Schema.Types.Mixed },
      newValue: { type: mongoose.Schema.Types.Mixed },
      changedBy: { type: ObjectId, ref: 'Person' },
      changedAt: { type: Date, default: Date.now }
    }],
    metadata: { type: Object }, // Flexible field for additional data  
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for Task collection
  db.tasks.createIndex({ assignedTo: 1 }); // Tasks by assignee
  db.tasks.createIndex({ createdBy: 1 }); // Tasks by creator
  db.tasks.createIndex({ "relatedPeople.personId": 1 }); // Tasks related to person
  db.tasks.createIndex({ status: 1 }); // Filter by status
  db.tasks.createIndex({ dueDate: 1 }); // Sort/filter by due date
  db.tasks.createIndex({ organization: 1 }); // Filter by organization
  db.tasks.createIndex({ project: 1 }); // Filter by project
  db.tasks.createIndex({ team: 1 }); // Filter by team
  db.tasks.createIndex({ tags: 1 }); // Search by tags
  db.tasks.createIndex({ aiGenerated: 1 }); // Filter AI generated tasks
  
  // Team Schema
  const TeamSchema = {
    _id: ObjectId,
    name: { type: String, required: true },
    description: { type: String },
    organization: { type: ObjectId, ref: 'Organization', required: true },
    leader: { type: ObjectId, ref: 'Person', required: true },
    members: [{ type: ObjectId, ref: 'Person' }],
    projects: [{ type: ObjectId, ref: 'Project' }],
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for Team collection
  db.teams.createIndex({ organization: 1 }); // Filter by organization
  db.teams.createIndex({ leader: 1 }); // Teams led by person
  db.teams.createIndex({ members: 1 }); // Teams with specific members
  
  // Project Schema
  const ProjectSchema = {
    _id: ObjectId,
    name: { type: String, required: true },
    description: { type: String },
    startDate: { type: Date },
    endDate: { type: Date },
    status: { 
      type: String, 
      enum: ['planning', 'active', 'on_hold', 'completed'], 
      default: 'planning' 
    },
    organization: { type: ObjectId, ref: 'Organization', required: true },
    team: { type: ObjectId, ref: 'Team' },
    leader: { type: ObjectId, ref: 'Person' },
    members: [{ type: ObjectId, ref: 'Person' }],
    tasks: [{ type: ObjectId, ref: 'Task' }],
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for Project collection
  db.projects.createIndex({ organization: 1 }); // Filter by organization
  db.projects.createIndex({ team: 1 }); // Filter by team
  db.projects.createIndex({ leader: 1 }); // Projects led by person
  db.projects.createIndex({ members: 1 }); // Projects with specific members
  db.projects.createIndex({ status: 1 }); // Filter by status
  
  // Organization Schema
  const OrganizationSchema = {
    _id: ObjectId,
    name: { type: String, required: true },
    description: { type: String },
    settings: {
      taskCategories: [String],
      priorityLevels: [String],
      customFields: [{
        name: { type: String },
        type: { type: String, enum: ['text', 'number', 'date', 'select', 'checkbox'] },
        options: [String], // For select type fields
        required: { type: Boolean, default: false }
      }]
    },
    createdAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for Organization collection
  db.organizations.createIndex({ name: 1 }); // Search by name
  
  // AI Training Data Schema (for storing data to improve AI predictions)
  const AITrainingDataSchema = {
    _id: ObjectId,
    personId: { type: ObjectId, ref: 'Person', required: true },
    dataType: { 
      type: String, 
      enum: ['task_pattern', 'task_completion', 'collaboration', 'speech_transcription'],
      required: true
    },
    data: { type: Object, required: true }, // Flexible schema based on dataType
    feedback: { 
      correct: { type: Boolean },
      adjustments: { type: Object }
    },
    createdAt: { type: Date, default: Date.now }
  }
  
  // Create indexes for AI Training Data collection
  db.aiTrainingData.createIndex({ personId: 1 }); // Filter by person
  db.aiTrainingData.createIndex({ dataType: 1 }); // Filter by data type
  db.aiTrainingData.createIndex({ createdAt: 1 }); // Time-based queries
  