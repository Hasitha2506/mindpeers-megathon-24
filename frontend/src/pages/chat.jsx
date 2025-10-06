import { useState, useEffect, useRef } from 'react';
import SentimentTrend from '../components/SentimentTrend';

export default function Chat({ user }) {
  const [showTrend, setShowTrend] = useState(false);    
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSeverity, setCurrentSeverity] = useState('SAFE');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!newMessage.trim() || loading) return

    setLoading(true)
    const messageToSend = newMessage.trim()
    
    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      text: messageToSend,
      isBot: false,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setNewMessage('')

    try {
      const response = await fetch('http://localhost:5000/api/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          user_id: user?.user_id || 'anonymous',
          message_text: messageToSend
        }),
      })
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', response.status, errorText);
        throw new Error('Failed to send message')
      }
      
      const data = await response.json()
      
      // Update severity if present in response
      if (data.analysis) {
        setCurrentSeverity(data.analysis.severity)
      }
      
      // Add bot reply with entities
      const botMessage = {
        id: Date.now() + 1,
        text: data.bot_reply,
        isBot: true,
        timestamp: new Date(),
        analysis: data.analysis
      }
      
      setMessages(prev => [...prev, botMessage])

      // Update the user message to include entities AND concern data
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? {...msg, entities: data.analysis.entities, analysis: data.analysis}
          : msg
      ))
      
    } catch (error) {
      console.error('Message error:', error)
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        text: "I'm having trouble responding right now. Please try again.",
        isBot: true,
        isError: true,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'IMMINENT':
        return 'bg-red-600'
      case 'DISTRESSED':
        return 'bg-orange-500'
      case 'ELEVATED':
        return 'bg-yellow-500'
      default:
        return 'bg-green-500'
    }
  }

  const quickSuggestions = [
    "I'm feeling really anxious and overwhelmed",
    "I've been having dark thoughts lately", 
    "I'm struggling with depression",
    "I'm having relationship problems",
    "I'm under a lot of stress at work",
    "I've been thinking about self-harm",
    "I feel completely alone and isolated"
  ]

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'IMMINENT':
        return '🚨'
      case 'DISTRESSED':
        return '⚠️'
      case 'ELEVATED':
        return '🔍'
      default:
        return '✅'
    }
  }

  const getSeverityMessage = (severity) => {
    switch (severity) {
      case 'IMMINENT':
        return 'IMMINENT RISK DETECTED - Please seek immediate help'
      case 'DISTRESSED':
        return 'High distress detected - We are here for you'
      case 'ELEVATED':
        return 'Elevated concern detected - We are listening'
      default:
        return 'You are safe - Continue sharing how you feel'
    }
  }

  const getEntityColor = (label) => {
    switch (label) {
      case 'Work': return 'bg-orange-100 text-orange-800'
      case 'School': return 'bg-purple-100 text-purple-800'
      case 'Family': return 'bg-green-100 text-green-800'
      case 'Relationship': return 'bg-pink-100 text-pink-800'
      case 'Person': return 'bg-blue-100 text-blue-800'
      case 'Location': return 'bg-indigo-100 text-indigo-800'
      case 'Health': return 'bg-red-100 text-red-800'
      case 'Financial': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getConcernColor = (label) => {
    switch (label) {
      case 'suicidal': return 'bg-red-100 text-red-800 border border-red-200'
      case 'self-harm': return 'bg-red-100 text-red-800 border border-red-200'
      case 'depression': return 'bg-blue-100 text-blue-800 border border-blue-200'
      case 'anxiety': return 'bg-purple-100 text-purple-800 border border-purple-200'
      case 'stress': return 'bg-orange-100 text-orange-800 border border-orange-200'
      case 'relationship': return 'bg-pink-100 text-pink-800 border border-pink-200'
      default: return 'bg-gray-100 text-gray-800 border border-gray-200'
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Trend View Toggle - MOVED OUTSIDE THE FORM */}
      <div className="mb-4 flex justify-end">
        <button
          onClick={() => setShowTrend(!showTrend)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
        >
          {showTrend ? '← Back to Chat' : '📊 View Mood Trends'}
        </button>
      </div>

      {showTrend ? (
        <SentimentTrend user={user} />
      ) : (
        <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
          {/* Severity Alert Banner */}
          {currentSeverity !== 'SAFE' && (
            <div className={`p-3 text-white text-center font-medium ${getSeverityColor(currentSeverity)}`}>
              <div className="flex items-center justify-center space-x-2">
                <span>{getSeverityIcon(currentSeverity)}</span>
                <span>{getSeverityMessage(currentSeverity)}</span>
                <span>{getSeverityIcon(currentSeverity)}</span>
              </div>
              {currentSeverity === 'IMMINENT' && (
                <div className="text-sm mt-1 bg-red-700 p-2 rounded">
                  <strong>Crisis Resources:</strong> National Suicide Prevention Lifeline: 988 (US) | Emergency: 911 | 
                  Crisis Text Line: Text HOME to 741741
                </div>
              )}
              {currentSeverity === 'DISTRESSED' && (
                <div className="text-sm mt-1 bg-orange-600 p-2 rounded">
                  <strong>Support Resources:</strong> You're not alone. Consider reaching out to a mental health professional or trusted person in your life.
                </div>
              )}
            </div>
          )}
          
          {/* Safe Status Banner */}
          {currentSeverity === 'SAFE' && (
            <div className="bg-green-500 text-white p-3 text-center font-medium">
              <div className="flex items-center justify-center space-x-2">
                <span>✅</span>
                <span>You're in a safe space. Feel free to share what's on your mind.</span>
                <span>✅</span>
              </div>
            </div>
          )}
          
          {/* Chat Header */}
          <div className="bg-blue-600 text-white p-4 rounded-t-lg">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Support Chat</h2>
                <p className="text-blue-100 text-sm">I'm here to listen and support you</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-blue-200">Current Status</div>
                <div className="flex items-center space-x-1">
                  <span className={`w-2 h-2 rounded-full ${
                    currentSeverity === 'IMMINENT' ? 'bg-red-400' :
                    currentSeverity === 'DISTRESSED' ? 'bg-orange-400' :
                    currentSeverity === 'ELEVATED' ? 'bg-yellow-400' : 'bg-green-400'
                  }`}></span>
                  <span className="text-sm font-medium">{currentSeverity}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <div className="text-6xl mb-4">💬</div>
                <p className="text-lg font-medium">Welcome to your safe space</p>
                <p className="text-sm max-w-md mx-auto mt-2">
                  This is a confidential space where you can share your thoughts and feelings. 
                  I'm here to listen without judgment.
                </p>
                
                {/* Quick Suggestions */}
                <div className="mt-6 max-w-md mx-auto">
                  <p className="text-sm text-gray-600 mb-3">Try starting with:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setNewMessage(suggestion)}
                        className="text-xs bg-blue-100 text-blue-700 px-3 py-2 rounded-full hover:bg-blue-200 transition-colors border border-blue-200"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                        message.isBot
                          ? 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                          : 'bg-blue-600 text-white rounded-br-none shadow-md'
                      } ${message.isError ? 'bg-red-100 border-red-300 text-red-800' : ''}`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                      
                      {/* Show entities for user messages */}
                      {!message.isBot && message.entities && message.entities.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="flex flex-wrap gap-1">
                            {message.entities.map((entity, index) => (
                              <span
                                key={index}
                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getEntityColor(entity.label)}`}
                              >
                                {entity.text} • {entity.label}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Show sentiment analysis for user messages */}
                      {!message.isBot && message.analysis && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <span>Sentiment: {message.analysis.polarity > 0 ? '😊' : message.analysis.polarity < -0.3 ? '😔' : '😐'}</span>
                            <span>•</span>
                            <span>Score: {message.analysis.polarity}</span>
                          </div>
                        </div>
                      )}
                      
                      {/* Show concern classification for user messages */}
                      {!message.isBot && message.analysis && message.analysis.concern && message.analysis.concern.label !== 'safe' && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">Detected Concern:</span>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConcernColor(message.analysis.concern.label)}`}>
                              {message.analysis.concern.label} 
                              <span className="ml-1 text-xs opacity-75">
                                ({Math.round(message.analysis.concern.confidence * 100)}%)
                              </span>
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {/* Show analysis details for bot messages that have it */}
                      {message.isBot && message.analysis && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <span>Analysis: {message.analysis.severity}</span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              message.analysis.severity === 'IMMINENT' ? 'bg-red-100 text-red-800' :
                              message.analysis.severity === 'DISTRESSED' ? 'bg-orange-100 text-orange-800' :
                              message.analysis.severity === 'ELEVATED' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {message.analysis.severity}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      <p className={`text-xs mt-2 ${
                        message.isBot ? 'text-gray-500' : 'text-blue-200'
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator */}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-none">
                      <div className="flex items-center space-x-3">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <div className="text-sm text-gray-600">
                          <span className="font-medium">MindPeers</span> is thinking...
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          
          {/* Quick Suggestions (when there are messages) */}
          {messages.length > 0 && (
            <div className="px-4 pt-2">
              <div className="flex flex-wrap gap-2">
                {quickSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setNewMessage(suggestion)}
                    className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors border border-blue-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input Area */}
          <form onSubmit={sendMessage} className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
            <div className="flex space-x-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Share what's on your mind..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !newMessage.trim()}
                className="bg-blue-600 text-white px-6 py-3 rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {loading ? 'Sending...' : 'Send'}
              </button>
            </div>
            <div className="text-xs text-gray-500 text-center mt-2">
              Your conversations are private and secure
            </div>
          </form>
        </div>
      )}
    </div>
  );
}