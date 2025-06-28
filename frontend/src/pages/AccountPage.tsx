import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/store';
import { authService } from '../services/auth';
import { User, Mail, Lock, Loader2, AlertCircle, Check } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../config/constants';

interface AccountInfo {
  email: string;
  fullName: string;
  phoneNumber: string;
}

export function AccountPage() {
  const navigate = useNavigate();
  const { user } = useStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showPasswordSection, setShowPasswordSection] = useState(false);
  
  const [accountInfo, setAccountInfo] = useState<AccountInfo>({
    email: '',
    fullName: '',
    phoneNumber: ''
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }

    fetchAccountInfo();
  }, [user, navigate]);

  const fetchAccountInfo = async () => {
    try {
      setLoading(true);
      const token = await authService.getAccessToken();
      const response = await axios.get(`${API_URL}/api/v1/users/${user?.id}/account`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccountInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch account info:', error);
      setError('Failed to load account information');
      // Use user data from auth if API fails
      if (user) {
        setAccountInfo({
          email: user.email || '',
          fullName: user.user_metadata?.full_name || '',
          phoneNumber: user.user_metadata?.phone_number || ''
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const updateAccount = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const token = await authService.getAccessToken();
      await axios.put(`${API_URL}/api/v1/users/${user?.id}/account`, accountInfo, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to update account:', error);
      setError('Failed to update account information');
    } finally {
      setSaving(false);
    }
  };

  const updatePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await authService.updatePassword(passwordData.newPassword);

      setSuccess(true);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      setShowPasswordSection(false);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to update password:', error);
      setError('Failed to update password');
    } finally {
      setSaving(false);
    }
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
      <div className="max-w-3xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Account Settings</h1>

        {/* Account Information */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <User className="w-5 h-5 mr-2" />
              Account Information
            </h2>
          </div>

          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={accountInfo.fullName}
                onChange={(e) => setAccountInfo({ ...accountInfo, fullName: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Mail className="w-4 h-4 inline mr-1" />
                Email Address
              </label>
              <input
                type="email"
                value={accountInfo.email}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
              />
              <p className="text-sm text-gray-500 mt-1">Email cannot be changed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                value={accountInfo.phoneNumber}
                onChange={(e) => setAccountInfo({ ...accountInfo, phoneNumber: e.target.value })}
                placeholder="+1 (555) 123-4567"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="pt-4">
              <button
                onClick={updateAccount}
                disabled={saving}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>

        {/* Password Section */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Lock className="w-5 h-5 mr-2" />
              Password & Security
            </h2>
          </div>

          <div className="p-6">
            {!showPasswordSection ? (
              <button
                onClick={() => setShowPasswordSection(true)}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Change Password
              </button>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={updatePassword}
                    disabled={saving}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    {saving ? 'Updating...' : 'Update Password'}
                  </button>
                  <button
                    onClick={() => {
                      setShowPasswordSection(false);
                      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

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
            <span className="text-green-700">Changes saved successfully!</span>
          </div>
        )}

        {/* Danger Zone */}
        <div className="mt-8 bg-white rounded-lg shadow border border-red-200">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-red-600 mb-4">Danger Zone</h2>
            <p className="text-gray-600 mb-4">
              Once you delete your account, there is no going back. Please be certain.
            </p>
            <button className="text-red-600 hover:text-red-700 font-medium">
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}