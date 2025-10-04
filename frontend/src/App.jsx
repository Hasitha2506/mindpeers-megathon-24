// src/App.jsx
import { useState, useEffect } from 'react'
import NavBar from './components/NavBar'
import Login from './pages/login'
import Consent from './pages/consent'
import Chat from './pages/chat'
import Admin from './pages/admin'

function App() {
  const [currentPage, setCurrentPage] = useState('login')
  const [user, setUser] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('Checking...')

  // Test backend connection
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ping')
        if (response.ok) {
          setConnectionStatus('Connected 💡')
        } else {
          setConnectionStatus('Disconnected ❌')
        }
      } catch (error) {
        setConnectionStatus('Disconnected ❌')
        console.log('Backend connection failed. Make sure Flask server is running on port 5000')
      }
    }

    checkConnection()
  }, [])

  // Load user from localStorage on app start
  useEffect(() => {
    const savedUser = localStorage.getItem('mindpeers_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
      setCurrentPage('chat') // Go directly to chat if user exists
    }
  }, [])

  // Save user to localStorage whenever it changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('mindpeers_user', JSON.stringify(user))
    } else {
      localStorage.removeItem('mindpeers_user')
    }
  }, [user])

  const handleLogin = (userData) => {
    setUser(userData)
    setCurrentPage('consent')
  }

  const handleConsent = () => {
    setCurrentPage('chat')
  }

  const handleLogout = () => {
    setUser(null)
    setCurrentPage('login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage}
        connectionStatus={connectionStatus}
        user={user}
        onLogout={handleLogout}
      />
      
      <div className="container mx-auto px-4 py-8">
        {currentPage === 'login' && <Login onLogin={handleLogin} setCurrentPage={setCurrentPage} />}
        {currentPage === 'consent' && <Consent user={user} onConsent={handleConsent} />}
        {currentPage === 'chat' && user && <Chat user={user} />}
        {currentPage === 'admin' && <Admin />}
        
        {/* Show error if trying to access chat without user */}
        {currentPage === 'chat' && !user && (
          <div className="text-center text-red-600">
            Please login first to access the chat.
          </div>
        )}
      </div>
    </div>
  )
}

export default App
