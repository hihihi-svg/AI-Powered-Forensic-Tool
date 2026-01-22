# AI-Powered Forensic Tool

A comprehensive forensic analysis system that combines speech recognition, AI-powered sketch generation, deepfake detection, and intelligent database management for law enforcement and investigative purposes.

## 🎯 Features

### Module A: Speech-to-Sketch Generation
- **Voice-Based Suspect Description**: Record audio descriptions of suspects
- **AI Sketch Generation**: Automatically generates forensic sketches using Stable Diffusion with ControlNet
- **Intelligent Search**: Finds matching suspects in the database using facial embeddings
- **Real-time Transcription**: Converts speech to text using Google Speech Recognition

### Module B: Image Upload & Analysis
- **Drag-and-Drop Interface**: Easy image upload functionality
- **Deepfake Detection**: Advanced AI-powered detection of manipulated images
- **Authenticity Verification**: Determines if images are real or AI-generated
- **Confidence Scoring**: Provides detailed confidence metrics for analysis results

### Module C: Deepfake Detection
- **Batch Processing**: Analyze multiple images simultaneously
- **Advanced Detection**: Uses state-of-the-art deep learning models
- **Detailed Reports**: Comprehensive analysis with confidence scores
- **Visual Feedback**: Clear indicators for real vs. fake images

### Module D: Database Management
- **Suspect Database**: Comprehensive storage and retrieval system
- **Advanced Search**: Similarity-based search using Qdrant vector database
- **CRUD Operations**: Full create, read, update, delete functionality
- **Recycle Bin**: Soft delete with recovery options
- **Analytics Dashboard**: Visual insights with charts and statistics

### 🆕 Session Management & Memory System
- **Session Tracking**: Automatic user session management with 24-hour persistence
- **Interaction History**: Logs all searches, views, generations, and detections
- **Evolving Memory**: Suspects "learn" from access patterns
  - Frequently accessed suspects get confidence boost (up to +30%)
  - Temporal decay for unused records (30-day half-life)
  - Reinforcement learning based on usage patterns
- **Memory Layers**: Clear separation of knowledge, context, and history
- **Backward Compatible**: All features work with or without sessions

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI/ML Models**:
  - Stable Diffusion v1.5 with ControlNet (Sketch generation)
  - Facenet-PyTorch (Face embeddings)
  - DeepFake detection models
- **Vector Database**: Qdrant (for similarity search and memory)
- **Session Management**: File-based JSON storage with automatic cleanup
- **Memory System**: Temporal decay and reinforcement learning
- **Speech Recognition**: Google Speech Recognition API
- **Image Processing**: PIL, OpenCV, torchvision

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with modern design
- **Charts**: Recharts for data visualization
- **HTTP Client**: Axios
- **Icons**: Lucide React

## 📋 Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- CUDA-capable GPU (recommended for AI models)
- Minimum 8GB RAM (16GB recommended)

## 🚀 Installation

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create necessary directories**:
   ```bash
   mkdir -p dataset models qdrant_storage
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

## 🎮 Running the Application

### Start the Backend Server

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8086 --reload
```

The backend API will be available at `http://localhost:8086`

### Start the Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
AI-Powered-Forensic-Tool/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── routes.py               # API endpoints
│   │   ├── services/
│   │   │   ├── sketch_service.py   # Speech-to-sketch generation
│   │   │   ├── deepfake_detection_service.py
│   │   │   ├── text_to_image_service.py
│   │   │   ├── qdrant_service.py   # Vector database operations
│   │   │   ├── session_service.py  # Session management (NEW)
│   │   │   └── memory_service.py   # Evolving memory (NEW)
│   │   └── utils/
│   │       └── embedding.py        # Face embedding utilities
│   ├── dataset/                    # Suspect image dataset
│   ├── models/                     # AI model storage
│   ├── qdrant_storage/            # Vector database storage
│   ├── sessions/                   # Session data storage (NEW)
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Main dashboard
│   │   │   ├── ModuleA.jsx        # Speech-to-Sketch
│   │   │   ├── ModuleB.jsx        # Image Upload
│   │   │   ├── ModuleC.jsx        # Deepfake Detection
│   │   │   └── ModuleD.jsx        # Database Management
│   │   ├── components/
│   │   │   └── AudioRecorder.jsx  # Audio recording component
│   │   ├── config/
│   │   │   └── api.js             # API config + SessionManager (UPDATED)
│   │   └── App.jsx                # Main application component
│   └── package.json               # Node dependencies
└── README.md
```

## 🔧 API Endpoints

### Suspects Management
- `GET /api/suspects` - List all suspects
- `GET /api/suspects/{id}` - Get suspect details
- `POST /api/suspects` - Add new suspect
- `PUT /api/suspects/{id}` - Update suspect
- `DELETE /api/suspects/{id}` - Delete suspect
- `GET /api/suspects/deleted` - List deleted suspects
- `POST /api/suspects/{id}/restore` - Restore deleted suspect

### AI Operations
- `POST /api/generate-sketch` - Generate sketch from audio description
- `POST /api/detect-deepfake` - Detect deepfakes in images
- `POST /api/search-similar` - Find similar faces in database

### 🆕 Session Management
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{session_id}` - Get session data
- `GET /api/sessions/{session_id}/history` - Get interaction history
- `POST /api/sessions/{session_id}/interactions` - Log interaction
- `GET /api/sessions/{session_id}/context` - Get session context
- `PUT /api/sessions/{session_id}/context` - Update session context
- `DELETE /api/sessions/{session_id}` - Delete session
- `POST /api/sessions/cleanup` - Clean up expired sessions

### 🆕 Memory Statistics
- `GET /api/memory/stats/{suspect_id}` - Get memory stats for suspect

## 🎨 Features in Detail

### Speech-to-Sketch Workflow
1. User records audio description of suspect
2. System transcribes audio to text using Google Speech Recognition
3. AI generates forensic sketch using Stable Diffusion + ControlNet
4. System extracts facial embeddings from generated sketch
5. Database search finds matching suspects based on similarity
6. Results displayed with confidence scores

### Deepfake Detection
- Analyzes images for signs of AI manipulation
- Provides confidence scores for authenticity
- Supports batch processing
- Visual indicators for detection results

### Database Management
- Vector-based similarity search using Qdrant
- Facial embedding extraction using Facenet
- Soft delete with recycle bin functionality
- Advanced filtering and search capabilities
- Analytics and visualization

### 🆕 Session Management & Memory System
**Session Tracking**:
- Automatic session creation and management
- 24-hour session persistence
- Interaction history logging (searches, views, generations, detections)
- Session context for investigation state

**Evolving Memory**:
- **Access Tracking**: Records how often suspects are viewed/matched
- **Confidence Boosting**: Frequently accessed suspects get up to +30% confidence boost
- **Temporal Decay**: Unused records decay with 30-day half-life
- **Reinforcement Learning**: Combines access frequency and recency

**Memory Layers**:
- **Knowledge**: Static suspect data (embeddings, metadata)
- **Context**: Current investigation state (per session)
- **History**: User interactions and access patterns

**Usage Example**:
```javascript
import { SessionManager } from './config/api';

// Initialize session
const sessionId = await SessionManager.getSessionId();

// Log a search interaction
await SessionManager.logInteraction('search', 
  'brown hair, blue eyes',
  { matches: 5, top_match: 'suspect_123' }
);

// Get interaction history
const history = await SessionManager.getHistory(20);

// Update investigation context
await SessionManager.updateContext({
  current_case: 'case_456',
  investigation_stage: 'initial_search'
});
```

## 🔐 Security Considerations

- All uploaded files are temporarily stored and can be configured for automatic cleanup
- API endpoints should be protected with authentication in production
- Database connections should use secure credentials
- CORS is configured for development; adjust for production deployment

## 📊 Performance Optimization

- GPU acceleration for AI model inference
- Efficient vector similarity search with Qdrant
- Image caching and optimization
- Lazy loading for frontend components
- API response caching where applicable

## 🐛 Troubleshooting

### Backend Issues

**Port already in use**:
```bash
# Windows
taskkill /F /IM python.exe
# Linux/Mac
pkill -f uvicorn
```

**Qdrant storage lock**:
```bash
# Remove lock files
rm -rf backend/qdrant_storage/.lock
```

**Model loading errors**:
- Ensure sufficient GPU memory
- Check CUDA installation
- Verify model files are downloaded

### Frontend Issues

**Port 5173 in use**:
```bash
# Kill the process using the port
npx kill-port 5173
```

**Build errors**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📝 Dataset Setup

The system requires a dataset of suspect images. Place images in:
```
backend/dataset/mini-CelebAMask-HQ-img/
```

Images should be:
- High quality (preferably 512x512 or higher)
- Clear facial features
- Proper lighting
- Frontal or near-frontal poses

## 🚢 Deployment

### Backend Deployment (Render/Railway)
1. Set environment variables
2. Configure build command: `pip install -r requirements.txt`
3. Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend Deployment (Vercel/Netlify)
1. Build command: `npm run build`
2. Output directory: `dist`
3. Set API URL environment variable

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Development Team

## 🙏 Acknowledgments

- Stable Diffusion and ControlNet teams
- Facenet-PyTorch contributors
- Qdrant vector database
- FastAPI and React communities

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

**Note**: This system is designed for law enforcement and authorized investigative purposes only. Ensure compliance with local laws and regulations regarding facial recognition and data privacy.
