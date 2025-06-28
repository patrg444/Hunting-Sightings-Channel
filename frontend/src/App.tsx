import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './components/Layout/Header';
import { LoadingSpinner } from './components/Layout/LoadingSpinner';
import { useStore } from './store/store';
import { authService } from './services/auth';
import { MapPage } from './pages/MapPage';
import { SettingsPage } from './pages/SettingsPage';
import { SubmitSightingPage } from './pages/SubmitSightingPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { SubscriptionPage } from './pages/SubscriptionPage';
import { AccountPage } from './pages/AccountPage';

function App() {
  const { isLoading, setUser, user } = useStore();

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
    <Router>
      <div className="h-screen flex flex-col">
        <Header />
        
        <div className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<MapPage />} />
            <Route 
              path="/settings" 
              element={user ? <SettingsPage /> : <Navigate to="/" />} 
            />
            <Route 
              path="/submit-sighting" 
              element={user ? <SubmitSightingPage /> : <Navigate to="/" />} 
            />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route 
              path="/subscription" 
              element={user ? <SubscriptionPage /> : <Navigate to="/" />} 
            />
            <Route 
              path="/account" 
              element={user ? <AccountPage /> : <Navigate to="/" />} 
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
