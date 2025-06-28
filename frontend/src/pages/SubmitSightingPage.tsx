import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/store';
import { Camera, MapPin, Calendar, FileText, Send, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../config/constants';
import { authService } from '../services/auth';

interface SightingFormData {
  species: string;
  description: string;
  sightingDate: string;
  location: {
    lat: number | null;
    lon: number | null;
    name: string;
  };
  imageUrl?: string;
}

const SPECIES_OPTIONS = [
  'Elk', 'Deer', 'Bear', 'Black Bear', 'Moose', 
  'Mountain Lion', 'Bighorn Sheep', 'Mountain Goat',
  'Pronghorn', 'White-tailed Deer', 'Mule Deer',
  'Turkey', 'Other'
];

export function SubmitSightingPage() {
  const navigate = useNavigate();
  const { user } = useStore();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState<SightingFormData>({
    species: '',
    description: '',
    sightingDate: new Date().toISOString().split('T')[0],
    location: {
      lat: null,
      lon: null,
      name: ''
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.species || !formData.description || !formData.location.name) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      
      const token = await authService.getAccessToken();
      
      const payload = {
        species: formData.species.toLowerCase(),
        raw_text: formData.description,
        sighting_date: formData.sightingDate,
        location_name: formData.location.name,
        source_type: 'user_submission',
        source_url: `user:${user?.id}`,
        confidence_score: 1.0,
        ...(formData.location.lat && formData.location.lon && {
          location: `POINT(${formData.location.lon} ${formData.location.lat})`
        })
      };

      await axios.post(`${API_URL}/api/v1/sightings`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err) {
      console.error('Failed to submit sighting:', err);
      setError('Failed to submit sighting. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleGetCurrentLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData(prev => ({
            ...prev,
            location: {
              ...prev.location,
              lat: position.coords.latitude,
              lon: position.coords.longitude
            }
          }));
        },
        (error) => {
          console.error('Error getting location:', error);
          setError('Could not get your current location');
        }
      );
    } else {
      setError('Geolocation is not supported by your browser');
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
            <Send className="h-6 w-6 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Sighting Submitted!</h2>
          <p className="text-gray-600">Thank you for contributing to wildlife tracking.</p>
          <p className="text-sm text-gray-500 mt-2">Redirecting to map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Submit Wildlife Sighting</h1>

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Species Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileText className="w-4 h-4 inline mr-1" />
              Species *
            </label>
            <select
              value={formData.species}
              onChange={(e) => setFormData({ ...formData, species: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select a species</option>
              {SPECIES_OPTIONS.map(species => (
                <option key={species} value={species}>{species}</option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              Sighting Date *
            </label>
            <input
              type="date"
              value={formData.sightingDate}
              onChange={(e) => setFormData({ ...formData, sightingDate: e.target.value })}
              max={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <MapPin className="w-4 h-4 inline mr-1" />
              Location *
            </label>
            <input
              type="text"
              placeholder="Location name (e.g., Rocky Mountain National Park, GMU 39)"
              value={formData.location.name}
              onChange={(e) => setFormData({ ...formData, location: { ...formData.location, name: e.target.value } })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            
            <button
              type="button"
              onClick={handleGetCurrentLocation}
              className="mt-2 text-sm text-blue-600 hover:text-blue-700"
            >
              Use my current location
            </button>
            
            {formData.location.lat && formData.location.lon && (
              <p className="mt-1 text-sm text-gray-500">
                Coordinates: {formData.location.lat.toFixed(6)}, {formData.location.lon.toFixed(6)}
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <FileText className="w-4 h-4 inline mr-1" />
              Description *
            </label>
            <textarea
              rows={4}
              placeholder="Describe the sighting... (behavior, number of animals, habitat, etc.)"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Photo Upload (Future Feature) */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center text-gray-600">
              <Camera className="w-5 h-5 mr-2" />
              <span className="text-sm">Photo upload coming soon!</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {submitting ? (
                <>Loading...</>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Submit Sighting
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>

        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-1">Tips for Good Sightings</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Be as specific as possible about the location</li>
            <li>• Include the number of animals if multiple were seen</li>
            <li>• Note any interesting behaviors or interactions</li>
            <li>• Mention the habitat type (meadow, forest, near water, etc.)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}