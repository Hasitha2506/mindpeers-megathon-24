// src/components/NavBar.jsx
export default function NavBar({ currentPage, setCurrentPage, connectionStatus, user, onLogout }) {
  const getStatusColor = () => {
    if (connectionStatus.includes('Connected')) return 'bg-green-500'
    if (connectionStatus.includes('Checking')) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold">MindPeers</h1>
            <span className={`text-sm px-2 py-1 rounded ${getStatusColor()}`}>
              {connectionStatus}
            </span>
            {user && (
              <span className="text-sm bg-blue-500 px-2 py-1 rounded">
                Welcome, {user.email}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <button 
                  onClick={() => setCurrentPage('chat')}
                  className={`px-3 py-2 rounded transition ${
                    currentPage === 'chat' ? 'bg-blue-700' : 'hover:bg-blue-500'
                  }`}
                >
                  Chat
                </button>
                <button 
                  onClick={() => setCurrentPage('admin')}
                  className={`px-3 py-2 rounded transition ${
                    currentPage === 'admin' ? 'bg-blue-700' : 'hover:bg-blue-500'
                  }`}
                >
                  Admin
                </button>
                <button 
                  onClick={onLogout}
                  className="px-3 py-2 rounded hover:bg-blue-500 transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <button 
                onClick={() => setCurrentPage('login')}
                className={`px-3 py-2 rounded transition ${
                  currentPage === 'login' ? 'bg-blue-700' : 'hover:bg-blue-500'
                }`}
              >
                Login
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
