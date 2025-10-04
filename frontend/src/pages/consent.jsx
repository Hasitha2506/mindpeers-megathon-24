// src/pages/Consent.jsx
import { useState } from 'react'

export default function Consent({ user, onConsent }) {
  const [loading, setLoading] = useState(false)

  const handleConsent = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    const formData = new FormData(e.target)
    const emergencyPhone = formData.get('emergencyPhone')
    
    try {
      const response = await fetch('http://localhost:5000/api/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          user_id: user.user_id,
          emergency_phone: emergencyPhone 
        }),
      })
      
      const data = await response.json()
      
      if (response.ok) {
        onConsent() // Use the callback
      } else {
        alert('Consent failed: ' + data.error)
      }
    } catch (error) {
      alert('Consent error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">Terms & Conditions</h2>
      
      <div className="bg-gray-50 p-4 rounded-lg mb-6 max-h-60 overflow-y-auto">
        <h3 className="font-semibold mb-3 text-lg">Mental Health Support Agreement</h3>
        
        <div className="text-sm text-gray-600 space-y-3">
          <p>
            <strong>Important Notice:</strong> This service provides AI-powered mental health support 
            and is not a substitute for professional medical advice, diagnosis, or treatment.
          </p>
          
          <div className="space-y-2">
            <h4 className="font-medium text-gray-800">Service Limitations:</h4>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>This is an automated system and may not understand complex mental health situations</li>
              <li>In case of emergency, contact local emergency services immediately</li>
              <li>For clinical diagnosis and treatment, consult qualified healthcare professionals</li>
            </ul>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-gray-800">Privacy & Data:</h4>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Your conversations are stored anonymously for analysis and improvement</li>
              <li>We prioritize your privacy but cannot guarantee absolute security</li>
              <li>Aggregate data may be used for research purposes</li>
            </ul>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-gray-800">User Responsibilities:</h4>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>You can stop using the service at any time</li>
              <li>Provide accurate emergency contact information if needed</li>
              <li>Use the service responsibly and in good faith</li>
            </ul>
          </div>
          
          <p className="text-xs text-gray-500 mt-3">
            By checking the box below, you acknowledge that you have read, understood, 
            and agree to these terms and conditions.
          </p>
        </div>
      </div>

      <form onSubmit={handleConsent} className="space-y-4">
        <div className="flex items-start space-x-3">
          <input
            type="checkbox"
            id="consent"
            name="consent"
            required
            className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mt-1"
          />
          <label htmlFor="consent" className="block text-sm text-gray-900">
            I have read, understood, and agree to the Terms & Conditions above. 
            I understand this is an AI support system and not professional medical care.
          </label>
        </div>
        
        <div>
          <label htmlFor="emergencyPhone" className="block text-sm font-medium text-gray-700 mb-1">
            Emergency Contact Phone (Optional)
          </label>
          <input
            type="tel"
            id="emergencyPhone"
            name="emergencyPhone"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="+1 (555) 123-4567"
          />
          <p className="text-xs text-gray-500 mt-1">
            Provide a trusted contact number for emergency situations (optional)
          </p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-medium"
        >
          {loading ? 'Processing...' : 'Continue to Chat'}
        </button>
      </form>
    </div>
  )
}