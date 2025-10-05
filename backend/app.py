# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
import re
from transformers import pipeline

# Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# Initialize VADER sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Load spaCy model with error handling
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded successfully!")
except OSError:
    print("❌ spaCy model not found. Using fallback.")
    nlp = None

# Load Hugging Face classifier with error handling
try:
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1
    )
    print("✅ Hugging Face classifier loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load classifier: {e}")
    classifier = None

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
    
    # Messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            is_bot BOOLEAN DEFAULT FALSE,
            polarity REAL,
            severity TEXT,
            concern_label TEXT,
            concern_confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Entities table
    c.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            entity_text TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages (id)
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

# Update database schema
def update_database_schema():
    """Update database schema to add missing columns"""
    try:
        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        
        # Check if concern_label column exists
        c.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add concern_label if it doesn't exist
        if 'concern_label' not in columns:
            c.execute('ALTER TABLE messages ADD COLUMN concern_label TEXT')
            print("Added concern_label column to messages table")
        
        # Add concern_confidence if it doesn't exist
        if 'concern_confidence' not in columns:
            c.execute('ALTER TABLE messages ADD COLUMN concern_confidence REAL')
            print("Added concern_confidence column to messages table")
            
        conn.commit()
        conn.close()
        print("Database schema updated successfully")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")

# Call initialization functions
init_db()
update_database_schema()

# Helper functions
def determine_severity(message_text, polarity, concern_label):
    """Determine severity level based on sentiment and keywords"""
    if not message_text:
        return "SAFE"
        
    message_lower = message_text.lower()
    
    # Check for imminent risk keywords
    imminent_keywords = [
        'kill myself', 'end my life', 'suicide', 'want to die', 
        'not want to live', 'end it all', 'better off dead',
        'no reason to live', 'cant go on', 'i want to end it',
        'harm to myself', 'harm', 'dark thoughts', 'suicidal',
        'ending it all', 'no point living', 'give up'
    ]

    # Check for self-harm keywords
    self_harm_keywords = [
        'cut myself', 'self harm', 'hurt myself', 'self injury',
        'bleeding myself', 'burn myself', 'self destructive',
        'cutting', 'self-harm', 'self harm', 'hurting myself'
    ]

    distressed_keywords = [
          'hopeless', 'helpless', 'worthless', 'empty inside',
        'cant cope', 'dont want to wake up', 'tired of living',
        'overwhelmed', 'anxious', 'stressed', 'burned out',
        'cant take it', 'cant do this', 'losing control'
    ]
    
    if any(keyword in message_lower for keyword in imminent_keywords + self_harm_keywords + distressed_keywords):
        return "IMMINENT"
    
    # Check sentiment-based severity
    if polarity < -0.6:
        return "DISTRESSED"
    elif polarity < -0.3:
        return "ELEVATED"
    elif concern_label in ["stress", "relationship"] and polarity < -0.1:
        return "ELEVATED"
    else:
        return "SAFE"

def classify_concern(message_text):
    """Classify mental health concerns using zero-shot classification"""
    if not classifier or not message_text:
        return "safe", 0.0
    
    # Define mental health concern categories
    candidate_labels = [
        "suicidal thoughts",
        "self harm", 
        "depression",
        "anxiety",
        "stress",
        "relationship issues",
        "family problems",
        "work stress",
        "academic pressure",
        "loneliness",
        "trauma",
        "grief",
        "anger issues",
        "sleep problems",
        "eating disorders",
        "general mental health"
    ]
    
    try:
        # Classify the message
        result = classifier(message_text, candidate_labels)
        
        # Get the top classification
        top_label = result['labels'][0]
        top_confidence = result['scores'][0]
        
        # Map to simpler categories for our system
        concern_map = {
            "suicidal thoughts": "suicidal",
            "self harm": "self-harm",
            "depression": "depression", 
            "anxiety": "anxiety",
            "stress": "stress",
            "work stress": "stress",
            "academic pressure": "stress",
            "relationship issues": "relationship",
            "family problems": "relationship",
            "loneliness": "depression",
            "trauma": "depression",
            "grief": "depression",
            "anger issues": "stress",
            "sleep problems": "anxiety",
            "eating disorders": "depression",
            "general mental health": "safe"
        }
        
        mapped_concern = concern_map.get(top_label, "safe")
        
        # Only return concerning labels if confidence is high enough
        if top_confidence > 0.5 and mapped_concern != "safe":
            return mapped_concern, top_confidence
        else:
            return "safe", top_confidence
            
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return "safe", 0.0

def analyze_emotional_tone(message):
    """Analyze emotional tone beyond basic polarity"""
    if not message:
        return {
            "polarity": 0.0,
            "emotional_tone": "neutral",
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0
        }
        
    sentiment_scores = sentiment_analyzer.polarity_scores(message)
    
    # Categorize emotional tone
    if sentiment_scores['compound'] <= -0.7:
        emotional_tone = "severely distressed"
    elif sentiment_scores['compound'] <= -0.3:
        emotional_tone = "moderately distressed" 
    elif sentiment_scores['compound'] <= 0.1:
        emotional_tone = "neutral"
    elif sentiment_scores['compound'] <= 0.5:
        emotional_tone = "moderately positive"
    else:
        emotional_tone = "very positive"
    
    return {
        "polarity": sentiment_scores['compound'],
        "emotional_tone": emotional_tone,
        "positive_score": sentiment_scores['pos'],
        "negative_score": sentiment_scores['neg'],
        "neutral_score": sentiment_scores['neu']
    }

def get_recent_conversation(user_id, limit=5):
    """Get recent conversation history"""
    try:
        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        c.execute('''
            SELECT message_text, is_bot, created_at 
            FROM messages 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        messages = c.fetchall()
        conn.close()
        return messages
    except Exception as e:
        print(f"Error getting recent conversation: {e}")
        return []

def get_entity_label(entity_type):
    """Convert spaCy entity types to user-friendly labels"""
    labels = {
        "PERSON": "Person",
        "ORG": "Organization", 
        "GPE": "Location",
        "EVENT": "Event",
        "DATE": "Date",
        "TIME": "Time"
    }
    return labels.get(entity_type, entity_type)

def extract_names_with_patterns(message_text):
    """Extract possible person names using regex patterns"""
    if not message_text:
        return []
        
    try:
        # Simple pattern for capitalized words (not at sentence start)
        pattern = r'(?<!\.\s)(?<!^)(?<!\n)(?<!\w\. )\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b'
        matches = re.findall(pattern, message_text)
        names = []
        for name in matches:
            # Avoid duplicates and very short names
            if len(name.split()) <= 3 and len(name) > 2:
                names.append({
                    "text": name,
                    "type": "PATTERN",
                    "label": "Person"
                })
        return names
    except Exception as e:
        print(f"Error in extract_names_with_patterns: {e}")
        return []

def extract_mental_health_keywords(message_text):
    """Extract mental health related keywords"""
    if not message_text:
        return []
        
    keywords = []
    message_lower = message_text.lower()
    
    # Expanded mental health contexts
    mental_health_terms = {
        "work": ["work", "job", "career", "boss", "colleague", "office", "employment", "workplace", "unemployment", "job stress", "job pressure", "work stress", "work pressure", "burnout"],
        "school": ["school", "college", "university", "exam", "test", "homework", "studies", "academic", "grades", "gpa", "professor", "teacher", "class", "assignment", "project", "thesis", "dissertation", "student", "student life", "school stress", "academic pressure"],
        "family": ["family", "parent", "mother", "father", "sibling", "child", "mom", "dad", "brother", "sister", "relative", "sista", "bro", "cousin"],
        "relationship": ["partner", "boyfriend", "girlfriend", "spouse", "relationship", "dating", "marriage", "divorce", "breakup", "ex", "significant other", "fiance", "fiancee", "lover", "hubby", "wifey", "husband", "wife", "gf", "bf", "romantic"],
        "friends": ["friend", "friends", "friendship", "buddy", "pal", "social circle", "companions", "mate", "bff", "bestie", "best friend", "close friend", "close friends", "friend group", "bro"],
        "social": ["social", "social life", "isolation", "lonely", "alone", "isolated"],
        "health": ["health", "doctor", "therapy", "medication", "treatment", "hospital", "clinic", "illness", "sick", "chronic", "condition", "disorder", "disease", "physical health", "mental health treatment", "therapy sessions", "therapist", "psychiatrist"],
        "financial": ["money", "financial", "bill", "debt", "expensive", "cost", "payment", "salary", "income", "expenses", "budget", "savings", "financial stress", "financial pressure", "broke", "poverty", "unemployed", "unemployment", "jobless"],
        "future": ["future", "career", "goals", "dreams", "aspirations", "plans", "uncertain", "uncertainty", "unknown", "goals", "ambitions", "hopes", "fears about future"],
        "self_esteem": ["confidence", "self-esteem", "self worth", "insecurity", "insecure"],
        "trauma": ["trauma", "abuse", "ptsd", " traumatic", "past experiences", "flashbacks", "nightmares", "assault", "harassment", "victim", "survivor", "molestation", "rape", "childhood trauma", "abuse"],
        "grief": ["grief", "loss", "mourning", "bereavement", "died", "passed away", "funeral", "loss of loved one", "loss of family member", "loss of friend"],
        "substance": ["alcohol", "drugs", "substance", "addiction", "drink", "smoke", "smoking", "drug use", "rehab", "detox", "substance abuse", "alcoholism", "drug addiction", "overdose","cutting", "burning"],
        "mental_health": ["depression", "anxiety", "stress", "panic attack", "mental health", "bipolar", "schizophrenia", "ocd", "ptsd", "adhd", "autism", "eating disorder", "self-harm", "suicidal thoughts","cutting", "burning", "sh"],
        "emotions": ["anger", "frustration", "sadness", "loneliness", "fear", "guilt", "shame", "jealousy", "envy", "resentment", "grief", "disappointment", "hopelessness", "helplessness", "overwhelmed", "numb"]
    }
    
    try:
        for category, terms in mental_health_terms.items():
            for term in terms:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, message_lower):
                    # Find the actual word used (for proper capitalization)
                    match = re.search(pattern, message_text, re.IGNORECASE)
                    if match:
                        # Check if we haven't already added this category
                        if not any(k['label'] == category.title() for k in keywords):
                            keywords.append({
                                "text": match.group(),
                                "type": "KEYWORD", 
                                "label": category.title()
                            })
                    break  # Only add one keyword per category
    except Exception as e:
        print(f"Error in extract_mental_health_keywords: {e}")
    
    return keywords

def extract_entities(message_text):
    """Extract named entities from message text"""
    entities = []
    
    if not message_text or not message_text.strip():
        return entities

    try:
        # Extract entities using spaCy if available
        if nlp:
            doc = nlp(message_text)
            for ent in doc.ents:
                # Filter for relevant entity types
                if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "DATE", "TIME"]:
                    entities.append({
                        "text": ent.text,
                        "type": ent.label_,
                        "label": get_entity_label(ent.label_)
                    })
        
        # Extract mental health keywords
        mental_health_keywords = extract_mental_health_keywords(message_text)
        entities.extend(mental_health_keywords)
    
        # Extract names using patterns
        additional_names = extract_names_with_patterns(message_text)
        entities.extend(additional_names)
        
    except Exception as e:
        print(f"Error extracting entities: {e}")
    
    return entities

def generate_bot_reply(user_message, severity="SAFE"):
    """Generate friendly, supportive bot replies"""
    if not user_message:
        return "I'm here to listen. Could you share what's on your mind?"
        
    user_message_lower = user_message.lower()
    
    # More comprehensive responses
    if any(word in user_message_lower for word in ['lonely', 'alone', 'isolated']):
        return "Feeling lonely can be really painful. That sense of isolation must be difficult. Would you like to talk about what's making you feel alone right now?"
    
    elif any(word in user_message_lower for word in ['overwhelmed', 'too much', 'cant handle']):
        return "When everything feels overwhelming, it can help to break things down. What's feeling like the most pressing thing right now?"
    
    elif any(word in user_message_lower for word in ['hopeless', 'pointless', 'nothing matters']):
        return "Hopelessness can make everything feel heavy. I'm really glad you're reaching out despite feeling this way. Can you tell me more about what's contributing to these feelings?"
    
    elif any(word in user_message_lower for word in ['sleep', 'insomnia', 'cant sleep']):
        return "Sleep struggles can really impact everything else. That sounds exhausting. How long has your sleep been affected?"
    
    # Add follow-up questions for better conversation flow
    if "?" in user_message:
        return "That's an important question. While I can offer support, for specific advice it's best to consult a mental health professional. How are you feeling about this situation?"
    
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

def generate_bot_reply_with_entities(user_message, severity="SAFE", entities=None):
    """Generate bot replies considering extracted entities"""
    if entities is None:
        entities = []
    
    if not user_message:
        return "I'm here to listen. Could you share what's on your mind?"
        
    user_message_lower = user_message.lower()
    
    # Crisis responses first
    if severity == "IMMINENT":
        return "I'm very concerned about what you're sharing. Your life is precious and there are people who want to help. Please call the National Mental Health Helpline at 1800-599-0019 right now. You don't have to go through this alone."

    elif severity == "DISTRESSED":
        return "I can hear that you're going through something really difficult right now. Thank you for reaching out. Would you like to talk more about what's making you feel this way? I'm here to listen."
    
    # Entity-aware responses
    entity_labels = [entity.get('label', '') for entity in entities]
    
    # Respond based on detected entities
    if "Friends" in entity_labels:
        return "Friendships and social connections can be really important for our wellbeing. It sounds like your relationships with friends are affecting you. What's been happening with your friends?"
    
    elif "Social" in entity_labels:
        return "Social situations can be challenging sometimes. That sense of isolation or social pressure must be really tough. Would you like to talk more about what social situations are affecting you?"
    
    elif "Work" in entity_labels:
        work_entities = [e['text'] for e in entities if e.get('label') == 'Work']
        work_context = f" about {', '.join(work_entities)}" if work_entities else ""
        return f"Work-related stress{work_context} can be really challenging. The pressure must feel overwhelming at times. What aspect of work is affecting you the most right now?"
    
    elif "School" in entity_labels:
        return "Academic pressure can feel incredibly heavy. It sounds like school is causing you significant stress. What specifically about school is weighing on you?"
    
    elif "Family" in entity_labels:
        family_entities = [e['text'] for e in entities if e.get('label') == 'Family']
        family_context = f" like {', '.join(family_entities)}" if family_entities else ""
        return f"Family dynamics{family_context} can be complex and emotionally draining. It takes courage to acknowledge when family relationships are difficult. Would you like to explore this more?"
    
    elif "Relationship" in entity_labels:
        return "Relationship challenges can touch some of our deepest emotions. That pain must feel really intense. What would feel most supportive to you right now as you navigate this?"
    
    elif "Health" in entity_labels:
        return "Health-related issues can be incredibly challenging. It's important to take care of both your physical and mental health. What specific health concerns are you facing right now?"

    elif "Financial" in entity_labels:
        return "Financial stress can be overwhelming. It's tough to manage money worries on top of everything else. What specific financial challenges are you dealing with right now?"
    
    elif "Future" in entity_labels:
        return "Uncertainty about the future can create a lot of anxiety. It's completely normal to feel this way when facing the unknown. What aspects of the future are causing you the most concern?"
    
    elif "Trauma" in entity_labels:
        return "Traumatic experiences can have a lasting impact on our mental health. It's important to process these feelings. What specific trauma would you like to talk about?"
    
    elif "Grief" in entity_labels:
        return "Grief and loss can be incredibly painful. It's okay to feel a wide range of emotions during this time. Would you like to share more about your loss and how you're feeling?"    
    
    elif "Substance" in entity_labels:
        return "Struggling with substance use can be really tough. It's a brave step to acknowledge this challenge. What kind of support do you think would help you the most right now?"       
    
    elif "Mental_Health" in entity_labels:
        return "Mental health challenges can feel isolating, but you're not alone. Many people face similar struggles. What specific mental health issues are you dealing with right now?"  
    
    elif "Emotions" in entity_labels:
        return "Emotions can be complex and difficult to navigate. That pain must feel really intense. What would feel most supportive to you right now as you navigate this?"
    
    elif "Self_Esteem" in entity_labels:
        return "How we feel about ourselves can deeply impact our daily life. It sounds like you're struggling with self-worth right now. Those feelings can be really painful. Would you like to explore what's affecting your self-esteem?"
    
    # Existing keyword-based responses
    if any(word in user_message_lower for word in ['sad', 'depressed', 'unhappy', 'down']):
        return "I'm really sorry you're feeling this way. It takes courage to share these feelings. Would you like to talk more about what's bothering you?"
    
    elif any(word in user_message_lower for word in ['anxious', 'nervous', 'worried', 'stress']):
        return "I understand anxiety can be overwhelming. Let's take a moment to breathe together. What specifically is causing you stress right now?"
    
    # Default empathetic response
    return "Thank you for sharing that with me. I'm listening and I care about what you're going through. Could you tell me more?"

def generate_bot_reply_with_context(user_message, severity, entities, concern_label, confidence):
    """Generate bot replies considering concern classification"""
    if not user_message:
        return "I'm here to listen. Could you share what's on your mind?"
    
    # Crisis responses first
    if severity == "IMMINENT":
        return "I'm very concerned about what you're sharing. Your life is precious and there are people who want to help right now. Please call the National Suicide Prevention Lifeline at 988 or text HOME to 741741. You don't have to face this alone."
    
    # Concern-specific responses
    if concern_label == "suicidal" and confidence > 0.7:
        return "I hear that you're having thoughts about ending your life. That sounds incredibly painful and overwhelming. Would you be willing to reach out to a crisis counselor? They're available 24/7 and it's completely confidential."
    
    elif concern_label == "self-harm" and confidence > 0.7:
        return "It sounds like you're experiencing urges to harm yourself. That must feel really overwhelming and scary. Can you tell me more about what's triggering these feelings? I'm here to listen without judgment."
    
    elif concern_label == "depression" and confidence > 0.6:
        return "The heaviness of depression can make everything feel overwhelming. Thank you for sharing that with me. What does this depressive state feel like for you right now?"
    
    elif concern_label == "anxiety" and confidence > 0.6:
        return "Anxiety can make it feel like everything is spinning out of control. That constant worry must be exhausting. What's the main thing causing you anxiety right now?"
    
    elif concern_label == "stress" and confidence > 0.6:
        return "Stress can build up and feel completely overwhelming. It sounds like you're carrying a heavy load right now. What aspects feel most pressing to you?"
    
    elif concern_label == "relationship" and confidence > 0.6:
        person_names = []
        if entities:
            person_names = [e['text'] for e in entities if e.get('label') == 'Person']
        if person_names:
            return f"Relationship challenges with {', '.join(person_names)} can touch some of our deepest emotions. That pain must feel really intense. What would feel most supportive to you right now?"
        else:
            return "Relationship issues can be really painful and complex. It takes courage to acknowledge when relationships are difficult. Would you like to explore what's happening?"
    
    # Fall back to entity-aware responses
    return generate_bot_reply_with_entities(user_message, severity, entities)

# Routes
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
        
        print(f"📨 Received message from user {user_id}: {message_text}")

        if not user_id or not message_text:
            return jsonify({"error": "User ID and message text are required"}), 400
        
        # Analyze sentiment
        sentiment_scores = sentiment_analyzer.polarity_scores(message_text)
        polarity = sentiment_scores['compound']
        
        print(f"📊 Sentiment analysis: {polarity}")

        # Classify concern
        concern_label, concern_confidence = classify_concern(message_text)
        print(f"🎯 Concern classification: {concern_label} (confidence: {concern_confidence:.2f})")

        # Determine severity
        severity = determine_severity(message_text, polarity, concern_label)
        print(f"🚨 Severity level: {severity}")

        # Extract entities
        entities = extract_entities(message_text)
        print(f"🔍 Extracted entities: {entities}")

        conn = sqlite3.connect('mindpeers.db')
        c = conn.cursor()
        
        # Save user message with all analysis data
        c.execute('''
            INSERT INTO messages (user_id, message_text, is_bot, polarity, severity, concern_label, concern_confidence)
            VALUES (?, ?, FALSE, ?, ?, ?, ?)
        ''', (user_id, message_text, polarity, severity, concern_label, concern_confidence))
        
        user_message_id = c.lastrowid
        
        # Save extracted entities (only if entities exist)
        if entities:
            for entity in entities:
                c.execute('''
                    INSERT INTO entities (message_id, entity_text, entity_type)
                    VALUES (?, ?, ?)
                ''', (user_message_id, entity.get('text', ''), entity.get('label', '')))
        
        # Generate bot reply
        bot_reply = generate_bot_reply_with_context(message_text, severity, entities, concern_label, concern_confidence)
        
        print(f"🤖 Bot reply: {bot_reply}")

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
                "sentiment_scores": sentiment_scores,
                "entities": entities,
                "concern": {
                    "label": concern_label,
                    "confidence": round(concern_confidence, 3)
                }
            }
        })
        
    except Exception as e:
        print(f"❌ Message error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting MindPeers backend server...")
    print("🌐 Server running on http://localhost:5000")
    print("📡 Ready to accept requests!")
    app.run(debug=True, port=5000, host='0.0.0.0')