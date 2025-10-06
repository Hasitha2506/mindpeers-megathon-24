import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function SentimentTrend({ user }) {
  const [trendData, setTrendData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user?.user_id) {
      fetchTrendData();
    }
  }, [user]);

  const fetchTrendData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching trend data for user:', user.user_id);
      
      const response = await fetch(`http://localhost:5000/api/trend/${user.user_id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Trend data received:', data);
      
      if (data.trend) {
        setTrendData(data.trend);
        setSummary(data.summary);
      } else {
        setTrendData([]);
      }
    } catch (error) {
      console.error('Error fetching trend data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <div className="text-6xl mb-4">❌</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error loading trends</h3>
        <p className="text-gray-500 mb-4">{error}</p>
        <button
          onClick={fetchTrendData}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!trendData.length) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No sentiment data yet</h3>
        <p className="text-gray-500">Start chatting to see your mood trends</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Mood Timeline</h2>
          <p className="text-gray-600">Your emotional journey</p>
        </div>
        {summary && (
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">
                {summary.mood_trend === 'improving' ? '📈' : 
                 summary.mood_trend === 'declining' ? '📉' : '➖'}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900 capitalize">
                  Mood {summary.mood_trend}
                </p>
                <p className="text-xs text-gray-500">
                  {summary.mood_slope > 0 ? '+' : ''}{summary.mood_slope} change
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis 
              dataKey="index" 
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              domain={[-1, 1]}
              tick={{ fontSize: 12 }}
            />
<Tooltip
  formatter={(value) => [value.toFixed(3), 'Sentiment']}
  labelFormatter={(value, name, props) => (
    props?.payload?.message_preview || value || ''
  )}
/>
            <Line 
              type="monotone" 
              dataKey="polarity" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: '#1d4ed8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="mt-6 grid grid-cols-3 gap-4 text-center">
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">{summary.total_messages}</p>
            <p className="text-sm text-blue-800">Messages</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {summary.current_mood > 0.1 ? '😊' : summary.current_mood < -0.1 ? '😔' : '😐'}
            </p>
            <p className="text-sm text-green-800">Current Mood</p>
          </div>
          <div className={`p-3 rounded-lg ${
            summary.mood_trend === 'improving' ? 'bg-green-50' : 
            summary.mood_trend === 'declining' ? 'bg-red-50' : 'bg-gray-50'
          }`}>
            <p className="text-2xl font-bold capitalize">
              {summary.mood_trend === 'improving' ? '📈' : 
               summary.mood_trend === 'declining' ? '📉' : '➖'}
            </p>
            <p className={`text-sm capitalize ${
              summary.mood_trend === 'improving' ? 'text-green-800' : 
              summary.mood_trend === 'declining' ? 'text-red-800' : 'text-gray-800'
            }`}>
              {summary.mood_trend}
            </p>
          </div>
        </div>
      )}

      <div className="mt-4 text-center">
        <button
          onClick={fetchTrendData}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Refresh Data
        </button>
      </div>
    </div>
  );
}