import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useStore } from '@/store/store';
import { authService } from '@/services/auth';
import { AuthModal } from '../Auth/AuthModal';
import { featureFlags } from '@/services/featureFlags';
import { User, Bell, CreditCard, LogOut, Menu, ChevronDown, Sun, Moon, Map, Table, Flame, MapPin, Lock } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, setSidebarOpen, isSidebarOpen, viewMode, setViewMode, mapVisualization, setMapVisualization } = useStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const hasTableAccess = featureFlags.hasFeature('tableView');

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    // Check for saved dark mode preference or default to system preference
    const savedDarkMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedDarkMode ? savedDarkMode === 'true' : prefersDark;
    
    setDarkMode(isDark);
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode.toString());
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="bg-green-700 dark:bg-gray-800 text-white shadow-lg transition-colors">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded-md hover:bg-green-600 dark:hover:bg-gray-700 lg:hidden"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>
            
            <Link to="/" className="ml-4 text-xl font-bold hover:text-green-100 transition-colors">
              Wildlife Sightings Channel
            </Link>
          </div>

          {/* Right side controls */}
          <div className="flex items-center space-x-4">
            {/* Map/Table Toggle - Only show on main page */}
            {location.pathname === '/' && (
              <>
                <div className="bg-green-600 dark:bg-gray-700 rounded-lg p-1 flex">
                  <button
                    onClick={() => setViewMode('map')}
                    className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors text-sm ${
                      viewMode === 'map'
                        ? 'bg-white text-green-700 dark:bg-gray-200 dark:text-gray-800'
                        : 'text-white hover:bg-green-500 dark:hover:bg-gray-600'
                    }`}
                    aria-label="Map view"
                  >
                    <Map className="w-4 h-4" />
                    <span className="font-medium">Map</span>
                  </button>
                  <button
                    onClick={() => {
                      if (hasTableAccess) {
                        setViewMode('table');
                      } else {
                        window.location.href = '/subscription';
                      }
                    }}
                    className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors text-sm ${
                      viewMode === 'table'
                        ? 'bg-white text-green-700 dark:bg-gray-200 dark:text-gray-800'
                        : 'text-white hover:bg-green-500 dark:hover:bg-gray-600'
                    } ${!hasTableAccess ? 'opacity-90' : ''}`}
                    aria-label="Table view"
                  >
                    <Table className="w-4 h-4" />
                    <span className="font-medium">Table</span>
                    {!hasTableAccess && <Lock className="w-3.5 h-3.5" />}
                  </button>
                </div>
                
                {/* Heat Map Toggle - Only show when in map view */}
                {viewMode === 'map' && (
                  <div className="bg-green-600 dark:bg-gray-700 rounded-lg p-1 flex">
                    <button
                      onClick={() => setMapVisualization('markers')}
                      className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors text-sm ${
                        mapVisualization === 'markers'
                          ? 'bg-white text-green-700 dark:bg-gray-200 dark:text-gray-800'
                          : 'text-white hover:bg-green-500 dark:hover:bg-gray-600'
                      }`}
                      aria-label="Markers view"
                    >
                      <MapPin className="w-4 h-4" />
                      <span className="font-medium">Markers</span>
                    </button>
                    <button
                      onClick={() => setMapVisualization('heatmap')}
                      className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors text-sm ${
                        mapVisualization === 'heatmap'
                          ? 'bg-white text-green-700 dark:bg-gray-200 dark:text-gray-800'
                          : 'text-white hover:bg-green-500 dark:hover:bg-gray-600'
                      }`}
                      aria-label="Heat map view"
                    >
                      <Flame className="w-4 h-4" />
                      <span className="font-medium">Heat Map</span>
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Dark mode toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-md hover:bg-green-600 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* User Menu */}
            <div className="relative" ref={dropdownRef}>
              {user ? (
                <div>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center p-2 rounded-md hover:bg-green-600 dark:hover:bg-gray-700"
                  >
                    <span className="mr-2">{user.email}</span>
                    <ChevronDown className="w-4 h-4" />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50">
                      <Link
                        to="/account"
                        className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <User className="w-4 h-4 mr-2" />
                        Account
                      </Link>
                      <Link
                        to="/settings"
                        className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <Bell className="w-4 h-4 mr-2" />
                        Notifications
                      </Link>
                      <Link
                        to="/subscription"
                        className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <CreditCard className="w-4 h-4 mr-2" />
                        Subscription
                      </Link>
                      <hr className="my-1 border-gray-200 dark:border-gray-700" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <LogOut className="w-4 h-4 mr-2" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="px-4 py-2 bg-white text-green-700 rounded-md hover:bg-gray-100 transition-colors"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </header>
  );
};