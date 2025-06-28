import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { User, Filters, Sighting, UserPreferences } from '@/types';

interface AppState {
  // Auth state
  user: User | null;
  isAuthenticated: boolean;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  isSidebarOpen: boolean;
  isMobileMenuOpen: boolean;
  viewMode: 'map' | 'table';
  
  // Sightings state
  sightings: Sighting[];
  selectedSighting: Sighting | null;
  totalSightings: number;
  currentPage: number;
  
  // Filter state
  filters: Filters;
  
  // User preferences
  preferences: UserPreferences | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  setMobileMenuOpen: (isOpen: boolean) => void;
  setSightings: (sightings: Sighting[], total: number) => void;
  setSelectedSighting: (sighting: Sighting | null) => void;
  setCurrentPage: (page: number) => void;
  updateFilters: (filters: Partial<Filters>) => void;
  clearFilters: () => void;
  setPreferences: (preferences: UserPreferences | null) => void;
  setViewMode: (mode: 'map' | 'table') => void;
}

const initialFilters: Filters = {};

export const useStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      isSidebarOpen: true,
      isMobileMenuOpen: false,
      viewMode: 'map',
      sightings: [],
      selectedSighting: null,
      totalSightings: 0,
      currentPage: 1,
      filters: initialFilters,
      preferences: null,
      
      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      setSidebarOpen: (isSidebarOpen) => set({ isSidebarOpen }),
      setMobileMenuOpen: (isMobileMenuOpen) => set({ isMobileMenuOpen }),
      setSightings: (sightings, totalSightings) => set({ sightings, totalSightings }),
      setSelectedSighting: (selectedSighting) => set({ selectedSighting }),
      setCurrentPage: (currentPage) => set({ currentPage }),
      updateFilters: (newFilters) => 
        set((state) => ({ 
          filters: { ...state.filters, ...newFilters },
          currentPage: 1, // Reset to first page when filters change
        })),
      clearFilters: () => set({ filters: initialFilters, currentPage: 1 }),
      setPreferences: (preferences) => set({ preferences }),
      setViewMode: (viewMode) => set({ viewMode }),
    }),
    {
      name: 'wildlife-sightings-store',
    }
  )
);
