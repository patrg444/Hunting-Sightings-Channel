import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { MapContainer } from './components/Map/MapContainer';
import { SightingsTable } from './components/Table/SightingsTable';
import { FilterSidebar } from './components/Filters/FilterSidebar';
import { Header } from './components/Layout/Header';
import { AppLayout } from './components/Layout/AppLayout';
import { LoadingSpinner } from './components/Layout/LoadingSpinner';
import { SettingsPage } from './pages/SettingsPage';
import { AccountPage } from './pages/AccountPage';
import { SubscriptionPage } from './pages/SubscriptionPage';
import { useStore } from './store/store';
import { authService } from './services/auth';

function AppContent() {
  const { isLoading, setUser, isSidebarOpen, viewMode } = useStore();

  useEffect(() => {
    // Check for authenticated user on mount
    const checkAuth = async () => {
      try {
        const user = await authService.getCurrentUser();
        setUser(user);
      } catch (error) {
        console.error('Auth check failed:', error);
      }
    };

    checkAuth();

    // Subscribe to auth changes
    const { data: authListener } = authService.onAuthStateChange((user) => {
      setUser(user);
    });

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, [setUser]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white dark:bg-gray-900">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={
        <div className="flex-1 flex relative overflow-hidden">
          {/* Filter Sidebar */}
          <div
            className={`
              absolute lg:relative z-20 h-full bg-white shadow-lg transition-all duration-300
              ${isSidebarOpen ? 'w-80' : 'w-0 lg:w-0'}
            `}
          >
            <FilterSidebar />
          </div>

          {/* Main Content Area */}
          <div className="flex-1 relative overflow-hidden">
            {viewMode === 'map' ? <MapContainer /> : <SightingsTable />}
          </div>
        </div>
      } />
      <Route path="/settings" element={
        <div className="flex-1 overflow-y-auto">
          <SettingsPage />
        </div>
      } />
      <Route path="/account" element={
        <div className="flex-1 overflow-y-auto">
          <AccountPage />
        </div>
      } />
      <Route path="/subscription" element={
        <div className="flex-1 overflow-y-auto">
          <SubscriptionPage />
        </div>
      } />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppLayout>
        <AppContent />
      </AppLayout>
    </Router>
  );
}

export default App;
