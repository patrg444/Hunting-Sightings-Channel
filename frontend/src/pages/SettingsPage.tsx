import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/store';
import { authService } from '../services/auth';
import { Bell, MapPin, CreditCard, Loader2, AlertCircle, Check } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../config/constants';

interface UserPreferences {
  emailNotifications: boolean;
  smsNotifications: boolean;
  notificationRadius: number;
  selectedSpecies: string[];
}

const SPECIES_OPTIONS = [
  'Deer', 'Elk', 'Moose', 'Bear', 'Turkey', 'Duck',
  'Pheasant', 'Grouse', 'Rabbit', 'Squirrel', 'Coyote', 'Wolf'
];

export function SettingsPage() {
  const navigate = useNavigate();
  const { user } = useStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications');

  const [preferences, setPreferences] = useState<UserPreferences>({
    emailNotifications: true,
    smsNotifications: false,
    notificationRadius: 10,
    selectedSpecies: []
  });

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    fetchPreferences();
  }, [user, navigate]);

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      const token = await authService.getAccessToken();
      const response = await axios.get(`${API_URL}/api/v1/users/${user?.id}/preferences`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPreferences(response.data);
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
      setError('Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      const token = await authService.getAccessToken();
      await axios.put(`${API_URL}/api/v1/users/${user?.id}/preferences`, preferences, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setError('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const toggleSpecies = (species: string) => {
    setPreferences(prev => ({
      ...prev,
      selectedSpecies: prev.selectedSpecies.includes(species)
        ? prev.selectedSpecies.filter(s => s !== species)
        : [...prev.selectedSpecies, species]
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('notifications')}
                className={`py-2 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'notifications'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Bell className="w-4 h-4 inline mr-2" />
                Notifications
              </button>
              <button
                onClick={() => setActiveTab('location')}
                className={`py-2 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'location'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <MapPin className="w-4 h-4 inline mr-2" />
                Location
              </button>
              <button
                onClick={() => setActiveTab('subscription')}
                className={`py-2 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'subscription'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <CreditCard className="w-4 h-4 inline mr-2" />
                Subscription
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
                  
                  <div className="space-y-4">
                    <label className="flex items-center justify-between">
                      <span className="text-gray-700">Email Notifications</span>
                      <input
                        type="checkbox"
                        checked={preferences.emailNotifications}
                        onChange={(e) => setPreferences({ ...preferences, emailNotifications: e.target.checked })}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </label>

                    <label className="flex items-center justify-between">
                      <div>
                        <span className="text-gray-700">SMS Notifications</span>
                        <span className="block text-sm text-gray-500">Coming soon</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={preferences.smsNotifications}
                        disabled
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 opacity-50"
                      />
                    </label>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Species Alerts</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Select which species you want to receive notifications about
                  </p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {SPECIES_OPTIONS.map(species => (
                      <label
                        key={species}
                        className={`
                          flex items-center justify-center px-4 py-2 border rounded-lg cursor-pointer
                          ${preferences.selectedSpecies.includes(species)
                            ? 'bg-blue-50 border-blue-500 text-blue-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                          }
                        `}
                      >
                        <input
                          type="checkbox"
                          checked={preferences.selectedSpecies.includes(species)}
                          onChange={() => toggleSpecies(species)}
                          className="sr-only"
                        />
                        <span>{species}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Location Tab */}
            {activeTab === 'location' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Location Settings</h3>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Notification Radius
                    </label>
                    <div className="flex items-center space-x-4">
                      <input
                        type="range"
                        min="1"
                        max="50"
                        value={preferences.notificationRadius}
                        onChange={(e) => setPreferences({ ...preferences, notificationRadius: parseInt(e.target.value) })}
                        className="flex-1"
                      />
                      <span className="text-gray-700 font-medium">{preferences.notificationRadius} miles</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      Receive notifications for sightings within this radius of your saved locations
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Subscription Tab */}
            {activeTab === 'subscription' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Subscription Management</h3>
                  <p className="text-gray-600 mb-4">
                    Manage your subscription and billing information
                  </p>
                  
                  <button
                    onClick={() => navigate('/subscription')}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                  >
                    Manage Subscription
                  </button>
                </div>
              </div>
            )}

            {/* Error/Success Messages */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0" />
                <span className="text-red-700">{error}</span>
              </div>
            )}

            {success && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start">
                <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-green-700">Settings saved successfully!</span>
              </div>
            )}

            {/* Save Button */}
            {(activeTab === 'notifications' || activeTab === 'location') && (
              <div className="mt-6 flex justify-end">
                <button
                  onClick={savePreferences}
                  disabled={saving}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}