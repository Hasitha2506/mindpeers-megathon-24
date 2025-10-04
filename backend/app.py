# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # Add this

# Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# Initialize VADER sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Database initialization
def init_db():
    conn = sqlite3.connect('mindpeers.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table (UPDATED with sentiment fields)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            is_bot BOOLEAN DEFAULT FALSE,
            polarity REAL,  -- Sentiment score from -1 to 1
            severity TEXT,  -- SAFE, ELEVATED, DISTRESSED, IMMINENT
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Consent table
    c.execute('''
        CREATE TABLE IF NOT EXISTS consent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            accepted BOOLEAN DEFAULT FALSE,
            emergency_phone TEXT,
            accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# Helper functions
def determine_severity(message_text, polarity):
    """Determine severity level based on sentiment and keywords"""
    message_lower = message_text.lower()
    
    # Check for imminent risk keywords
    imminent_keywords = ['kill myself', 'end my life', 'suicide', 'want to die', 'not want to live']
    if any(keyword in message_lower for keyword in imminent_keywords):
        return "IMMINENT"
    
    # Check sentiment-based severity
    if polarity < -0.6:
        return "DISTRESSED"
    elif polarity < -0.3:
        return "ELEVATED"
    else:
        return "SAFE"

def generate_bot_reply(user_message, severity="SAFE"):
    """Generate friendly, supportive bot replies"""
    user_message_lower = user_message.lower()
    
    # Custom responses based on severity
    if severity == "IMMINENT":
        return "I'm very concerned about what you're sharing. Your life is precious. Please contact emergency services immediately or call a crisis helpline. You're not alone - there are people who want to help you right now."
    
    elif severity == "DISTRESSED":
        return "I can hear that you're going through something really difficult right now. Thank you for reaching out. Would you like to talk more about what's making you feel this way? I'm here to listen."
    
    # Simple keyword-based responses
    if any(word in user_message_lower for word in ['sad', 'depressed', 'unhappy', 'down']):
        return "I'm really sorry you're feeling this way. It takes courage to share these feelings. Would you like to talk more about what's bothering you?"
    
    elif any(word in user_message_lower for word in ['anxious', 'nervous', 'worried', 'stress']):
        return "I understand anxiety can be overwhelming. Let's take a moment to breathe together. What specifically is causing you stress right now?"
    
    elif any(word in user_message_lower for word in ['angry', 'mad', 'frustrated', 'upset']):
        return "It's completely normal to feel angry sometimes. Would it help to talk about what triggered these feelings?"
    
    elif any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'start']):
        return "Hello! I'm here to listen and support you. How are you feeling today?"
    
    elif any(word in user_message_lower for word in ['help', 'support', 'need help']):
        return "I'm here for you. You're not alone in this. Can you tell me more about what kind of support you're looking for?"
    
    elif any(word in user_message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! I'm glad I can be here for you. Remember, reaching out is a sign of strength."
    
    # Default empathetic responses
    else:
        return "Thank you for sharing that with me. I'm listening and I care about what you're going through. Could you tell me more?"

# ROUTES - Define all routes AFTER app is created

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "Backend is running!"})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        email = data.get('email')
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT id, email FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if not user:
            # Create new user
            c.execute('INSERT INTO users (email) VALUES (?)', (email,))
            user_id = c.lastrowid
            print(f"✅ New user created: {email} (ID: {user_id})")
        else:
            user_id = user[0]
            print(f"✅ Existing user logged in: {email} (ID: {user_id})")
        
        conn.commit()
        
        return jsonify({
            "user_id": user_id,
            "email": email,
            "message": "Login successful"
        })
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/consent', methods=['POST'])
def consent():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        user_id = data.get('user_id')
        emergency_phone = data.get('emergency_phone', '')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        
        # Check if consent already exists
        c.execute('SELECT id FROM consent WHERE user_id = ?', (user_id,))
        existing_consent = c.fetchone()
        
        if existing_consent:
            # Update existing consent
            c.execute('''
                UPDATE consent 
                SET accepted = TRUE, emergency_phone = ?, accepted_at = ?
                WHERE user_id = ?
            ''', (emergency_phone, datetime.now(), user_id))
            print(f"✅ Consent updated for user ID: {user_id}")
        else:
            # Create new consent
            c.execute('''
                INSERT INTO consent (user_id, accepted, emergency_phone)
                VALUES (?, TRUE, ?)
            ''', (user_id, emergency_phone))
            print(f"✅ Consent created for user ID: {user_id}")
        
        conn.commit()
        
        return jsonify({
            "message": "Consent recorded successfully",
            "user_id": user_id
        })
        
    except Exception as e:
        print(f"❌ Consent error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/message', methods=['POST'])
def handle_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        user_id = data.get('user_id')
        message_text = data.get('message_text')
        
        print(f"📨 Received message from user {user_id}: {message_text}")  # Debug log
        
        if not user_id or not message_text:
            return jsonify({"error": "User ID and message text are required"}), 400
        
        # Analyze sentiment
        sentiment_scores = sentiment_analyzer.polarity_scores(message_text)
        polarity = sentiment_scores['compound']
        
        print(f"📊 Sentiment analysis: {polarity}")  # Debug log
        
        # Determine severity based on sentiment and keywords
        severity = determine_severity(message_text, polarity)
        
        print(f"🚨 Severity level: {severity}")  # Debug log
        
        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        
        # Save user message with sentiment data
        c.execute('''
            INSERT INTO messages (user_id, message_text, is_bot, polarity, severity)
            VALUES (?, ?, FALSE, ?, ?)
        ''', (user_id, message_text, polarity, severity))
        
        user_message_id = c.lastrowid
        
        # Generate bot reply
        bot_reply = generate_bot_reply(message_text, severity)
        
        print(f"🤖 Bot reply: {bot_reply}")  # Debug log
        
        # Save bot message
        c.execute('''
            INSERT INTO messages (user_id, message_text, is_bot)
            VALUES (?, ?, TRUE)
        ''', (user_id, bot_reply))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "bot_reply": bot_reply,
            "analysis": {
                "polarity": round(polarity, 3),
                "severity": severity,
                "sentiment_scores": sentiment_scores
            }
        })
        
    except Exception as e:
        print(f"❌ Message error: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show the full error stack
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting MindPeers backend server...")
    init_db()
    print("🌐 Server running on http://localhost:5000")
    print("📡 Ready to accept requests!")
    app.run(debug=True, port=5000, host='0.0.0.0')
# Ensure all routes and database initialization are defined after app creation