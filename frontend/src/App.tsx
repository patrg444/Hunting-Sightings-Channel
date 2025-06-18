import React, { useEffect } from 'react';
import { MapContainer } from './components/Map/MapContainer';
import { FilterSidebar } from './components/Filters/FilterSidebar';
import { Header } from './components/Layout/Header';
import { LoadingSpinner } from './components/Layout/LoadingSpinner';
import { useStore } from './store/store';
import { authService } from './services/auth';

function App() {
  const { isLoading, setUser, isSidebarOpen } = useStore();

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
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <Header />
      
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

        {/* Map Container */}
        <div className="flex-1 relative">
          <MapContainer />
        </div>
      </div>
    </div>
  );
}

export default App;
