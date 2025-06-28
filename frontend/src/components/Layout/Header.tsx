import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useStore } from '@/store/store';
import { authService } from '@/services/auth';
import { Map, Plus, Settings, CreditCard, User, LogOut, Menu } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, setSidebarOpen, isSidebarOpen } = useStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await authService.logout();
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-primary-700 text-white shadow-lg">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-6">
            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-md hover:bg-primary-600 lg:hidden"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <Link to="/" className="flex items-center space-x-2">
              <Map className="w-6 h-6" />
              <h1 className="text-xl font-bold">
                Wildlife Sightings Channel
              </h1>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden lg:flex items-center space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/') ? 'bg-primary-800' : 'hover:bg-primary-600'
                }`}
              >
                Map
              </Link>
              {user && (
                <>
                  <Link
                    to="/submit-sighting"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center ${
                      isActive('/submit-sighting') ? 'bg-primary-800' : 'hover:bg-primary-600'
                    }`}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Submit Sighting
                  </Link>
                  <Link
                    to="/subscription"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive('/subscription') ? 'bg-primary-800' : 'hover:bg-primary-600'
                    }`}
                  >
                    Subscription
                  </Link>
                </>
              )}
            </nav>
          </div>

          {/* User Menu */}
          <div className="relative">
            {user ? (
              <div>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center p-2 rounded-md hover:bg-primary-600"
                >
                  <span className="mr-2">{user.email}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg py-1 z-50">
                    <Link
                      to="/account"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <User className="w-4 h-4 mr-2" />
                      Account Settings
                    </Link>
                    <Link
                      to="/settings"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Preferences
                    </Link>
                    <Link
                      to="/subscription"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <CreditCard className="w-4 h-4 mr-2" />
                      Subscription
                    </Link>
                    <hr className="my-1" />
                    <button
                      onClick={handleLogout}
                      className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <span className="text-sm">Please log in</span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
