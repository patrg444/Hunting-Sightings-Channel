import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Header } from './Header';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isMainPage = location.pathname === '/';

  useEffect(() => {
    // Apply no-overscroll class to html element for main page
    if (isMainPage) {
      document.documentElement.classList.add('no-overscroll');
      document.body.classList.add('no-overscroll');
    } else {
      document.documentElement.classList.remove('no-overscroll');
      document.body.classList.remove('no-overscroll');
    }

    return () => {
      document.documentElement.classList.remove('no-overscroll');
      document.body.classList.remove('no-overscroll');
    };
  }, [isMainPage]);

  return (
    <div className={`h-screen flex flex-col ${isMainPage ? 'overflow-hidden' : ''}`}>
      <Header />
      {children}
    </div>
  );
};