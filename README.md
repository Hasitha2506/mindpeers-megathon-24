# MindPeers - Mental Health Support Chatbot

## 🧠 Overview
MindPeers is an AI-powered mental health support chatbot that provides empathetic conversations, sentiment analysis, and crisis detection. The system analyzes user messages for emotional distress and provides appropriate support responses while maintaining user privacy and safety.

## 🚀 Features

### Core Functionality
- **Real-time Chat Interface** - Supportive conversations with AI
- **Sentiment Analysis** - VADER sentiment analysis for emotional tone detection
- **Crisis Detection** - Multi-level severity assessment (SAFE → ELEVATED → DISTRESSED → IMMINENT)
- **Entity Extraction** - Identifies key topics (work, relationships, health, etc.)
- **Concern Classification** - AI-powered mental health concern categorization
- **User Management** - Secure user authentication and conversation history

### Technical Capabilities
- **Backend**: Flask REST API with SQLite database
- **Frontend**: React.js with responsive design
- **AI/ML**: 
  - spaCy for entity recognition
  - Hugging Face Transformers for zero-shot classification
  - VADER for sentiment analysis
- **Security**: CORS enabled, input validation, error handling

## 🛠 Tech Stack

### Backend
- **Framework**: Flask
- **Database**: SQLite3
- **AI/ML Libraries**:
  - `transformers` (Hugging Face)
  - `spacy` (en_core_web_sm)
  - `vaderSentiment`
- **Other**: flask-cors, regex

### Frontend
- **Framework**: React.js
- **Styling**: Tailwind CSS
- **State Management**: React Hooks

## 📁 Project Structure

```
mindpeers-megathon-24/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── mindpeers.db           # SQLite database
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Chat.jsx       # Main chat component
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

## 🔧 Installation & Setup

### Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start the server
python app.py
```
Server runs on: `http://localhost:5000`

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs on: `http://localhost:5173`

## 🗄 Database Schema

### Tables
- **users**: User accounts and profiles
- **messages**: Chat messages with sentiment/severity analysis
- **entities**: Extracted entities from messages
- **consent**: User consent records

## 🔍 Analysis Features

### Severity Levels
1. **SAFE** ✅ - Normal conversation
2. **ELEVATED** 🔍 - Mild concern detected
3. **DISTRESSED** ⚠️ - High distress detected
4. **IMMINENT** 🚨 - Crisis situation detected

### Entity Detection
- Work, School, Family, Relationship, Health
- Financial, Future, Trauma, Grief, Substance
- Mental Health, Emotions, Self-Esteem

### Concern Classification
- suicidal, self-harm, depression, anxiety
- stress, relationship, and more...

## 🎯 API Endpoints

### `POST /api/login`
User authentication and registration
```json
{
  "email": "user@example.com"
}
```

### `POST /api/consent`
User consent management
```json
{
  "user_id": 1,
  "emergency_phone": "+911234567890"
}
```

### `POST /api/message`
Main chat endpoint
```json
{
  "user_id": 1,
  "message_text": "I've been feeling really anxious lately"
}
```

### `GET /api/ping`
Health check endpoint

## 🛡 Safety Features

- **Crisis Detection**: Automatic detection of high-risk messages
- **Emergency Resources**: Immediate support contact information
- **Privacy Protection**: Secure data handling and storage
- **Consent Management**: User agreement for data processing

## 🚦 Current Status

### ✅ Working Features
- User authentication and session management
- Real-time chat interface
- Sentiment analysis and severity detection
- Entity extraction and concern classification
- Database persistence
- Error handling and validation

### 🚧 Known Issues & Fixes Applied
1. **Fixed**: 500 Internal Server Error - Message text clearing before API call
2. **Fixed**: Database schema mismatch - Added missing columns
3. **Fixed**: Entity extraction errors - Added null checks and error handling
4. **Fixed**: Indentation errors in Python code
5. **Fixed**: Missing function definitions

### 📋 Pending Improvements
- [ ] Update Indian helpline contacts in crisis responses
- [ ] Hide analysis labels from user view
- [ ] Implement full-screen responsive UI
- [ ] Add message history and context awareness
- [ ] Improve bot response quality and personalization

## 🔮 Future Enhancements

### Short-term
- Enhanced crisis intervention protocols
- Multi-language support
- Advanced analytics dashboard
- Mobile app development

### Long-term
- Therapist matching system
- Group support features
- Progress tracking and insights
- Integration with healthcare providers

## 👥 Team
Developed for MindPeers Megathon 2024 - Mental Health Track

## 📄 License
This project is developed for educational and competition purposes.

---

**Note**: This is a support system, not a replacement for professional mental healthcare. Always encourage users to seek professional help when needed.
