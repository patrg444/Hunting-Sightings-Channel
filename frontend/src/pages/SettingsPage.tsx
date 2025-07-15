import React, { useState, useEffect } from 'react';
import { Bell, Mail, Smartphone, MapPin, Save } from 'lucide-react';
import { useStore } from '@/store/store';
import api from '@/services/api';

export const SettingsPage: React.FC = () => {
  const { user, addToast } = useStore();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);
  const [sightingAlerts, setSightingAlerts] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);
  const [locationAlerts, setLocationAlerts] = useState(true);
  const [alertRadius, setAlertRadius] = useState('25');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        const { data } = await api.get('/api/v1/notifications/preferences');
        if (data) {
          setEmailNotifications(data.email_notifications ?? true);
          setSightingAlerts(data.sighting_alerts ?? true);
          setWeeklyDigest(data.weekly_digest ?? false);
          setPushNotifications(data.push_notifications ?? false);
          setLocationAlerts(data.location_alerts ?? true);
          setAlertRadius(String(data.alert_radius ?? 25));
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
        
        // If the API endpoint doesn't exist yet, just use defaults
        // This is not an error from the user's perspective
        console.log('Using default notification preferences');
      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, [user, addToast]);

  const handleSave = async () => {
    if (!user) {
      addToast({
        type: 'error',
        title: 'Not logged in',
        message: 'Please log in to save preferences'
      });
      return;
    }

    setSaving(true);
    
    try {
      // Save notification preferences
      await api.put('/api/v1/notifications/preferences', {
        email_notifications: emailNotifications,
        sighting_alerts: sightingAlerts,
        weekly_digest: weeklyDigest,
        push_notifications: pushNotifications,
        location_alerts: locationAlerts,
        alert_radius: parseInt(alertRadius)
      });
      
      addToast({
        type: 'success',
        title: 'Preferences saved',
        message: 'Your notification preferences have been updated'
      });
    } catch (error) {
      console.error('Failed to save preferences:', error);
      addToast({
        type: 'error',
        title: 'Save failed',
        message: 'Failed to save preferences. Please try again.'
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading preferences...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
            <Bell className="w-8 h-8 mr-3 text-green-600" />
            Notifications
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage how you receive updates about wildlife sightings
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-6">
          {/* Email Notifications */}
          <div className="border-b border-gray-200 pb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <Mail className="w-5 h-5 mr-2 text-gray-600" />
              Email Notifications
            </h2>
            
            <div className="space-y-4">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                  className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Enable email notifications</span>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Receive emails about new sightings in your area</p>
                </div>
              </label>

              <label className="flex items-start ml-7">
                <input
                  type="checkbox"
                  checked={sightingAlerts}
                  onChange={(e) => setSightingAlerts(e.target.checked)}
                  disabled={!emailNotifications}
                  className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded disabled:opacity-50"
                />
                <div className="ml-3">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Real-time sighting alerts</span>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Get notified immediately when new sightings are reported</p>
                </div>
              </label>

              <label className="flex items-start ml-7">
                <input
                  type="checkbox"
                  checked={weeklyDigest}
                  onChange={(e) => setWeeklyDigest(e.target.checked)}
                  disabled={!emailNotifications}
                  className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded disabled:opacity-50"
                />
                <div className="ml-3">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Weekly digest</span>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Receive a summary of sightings every Monday</p>
                </div>
              </label>
            </div>
          </div>

          {/* Push Notifications */}
          <div className="border-b border-gray-200 pb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <Smartphone className="w-5 h-5 mr-2 text-gray-600" />
              Push Notifications
            </h2>
            
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={pushNotifications}
                onChange={(e) => setPushNotifications(e.target.checked)}
                className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
              <div className="ml-3">
                <span className="font-medium text-gray-700">Enable push notifications</span>
                <p className="text-sm text-gray-500">Receive notifications on your device (requires Pro subscription)</p>
              </div>
            </label>
          </div>

          {/* Location Settings */}
          <div className="pb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-gray-600" />
              Location Alerts
            </h2>
            
            <div className="space-y-4">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={locationAlerts}
                  onChange={(e) => setLocationAlerts(e.target.checked)}
                  className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <div className="ml-3">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Location-based alerts</span>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Only receive notifications for sightings near you</p>
                </div>
              </label>

              <div className="ml-7">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alert radius
                </label>
                <select
                  value={alertRadius}
                  onChange={(e) => setAlertRadius(e.target.value)}
                  disabled={!locationAlerts}
                  className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-md disabled:opacity-50"
                >
                  <option value="10">10 miles</option>
                  <option value="25">25 miles</option>
                  <option value="50">50 miles</option>
                  <option value="100">100 miles</option>
                  <option value="unlimited">Unlimited</option>
                </select>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full sm:w-auto px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </div>

        {/* Pro Features Notice */}
        {!user || true /* Replace with actual subscription check */ && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Upgrade to Pro</strong> to unlock push notifications, unlimited alert radius, and priority delivery of notifications.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};