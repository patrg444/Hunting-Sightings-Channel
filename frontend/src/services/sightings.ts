import api from './api';
import type { Sighting, SightingStats, Filters, PaginatedResponse } from '@/types';

// Sightings API service
export const sightingsService = {
  // Get paginated sightings with filters
  async getSightings(filters: Filters, page = 1, pageSize = 20): Promise<PaginatedResponse<Sighting>> {
    const params = new URLSearchParams();
    
    if (filters.gmu) params.append('gmu', filters.gmu.toString());
    if (filters.gmuList && filters.gmuList.length > 0) {
      params.append('gmu_list', filters.gmuList.join(','));
    }
    if (filters.species) params.append('species', filters.species);
    if (filters.speciesList && filters.speciesList.length > 0) {
      params.append('species_list', filters.speciesList.join(','));
    }
    if (filters.source) params.append('source', filters.source);
    if (filters.sourceList && filters.sourceList.length > 0) {
      params.append('source_list', filters.sourceList.join(','));
    }
    if (filters.startDate) params.append('start_date', filters.startDate.toISOString().split('T')[0]);
    if (filters.endDate) params.append('end_date', filters.endDate.toISOString().split('T')[0]);
    if (filters.lat) params.append('lat', filters.lat.toString());
    if (filters.lon) params.append('lon', filters.lon.toString());
    if (filters.radiusMiles) params.append('radius_miles', filters.radiusMiles.toString());
    
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const { data } = await api.get<PaginatedResponse<Sighting>>(`/sightings?${params}`);
    return data;
  },

  // Get sighting by ID
  async getSightingById(id: string): Promise<Sighting> {
    const { data } = await api.get<Sighting>(`/sightings/${id}`);
    return data;
  },

  // Get sightings statistics
  async getStats(days = 30): Promise<SightingStats> {
    const { data } = await api.get<SightingStats>(`/sightings/stats?days=${days}`);
    return data;
  },

  // Get unique species list
  async getSpeciesList(): Promise<string[]> {
    const stats = await this.getStats(365); // Get last year's data
    return Object.keys(stats.species_counts).sort();
  },

  // Get unique sources list
  async getSourcesList(): Promise<string[]> {
    const stats = await this.getStats(365);
    return Object.keys(stats.source_counts).sort();
  },
};

// User preferences API service
export const userService = {
  // Get user preferences
  async getPreferences() {
    const { data } = await api.get('/users/prefs');
    return data;
  },

  // Update user preferences
  async updatePreferences(preferences: Partial<{
    email_notifications: boolean;
    notification_time: string;
    gmu_filter: number[];
    species_filter: string[];
  }>) {
    const { data } = await api.put('/users/prefs', preferences);
    return data;
  },

  // Reset preferences to defaults
  async resetPreferences() {
    const { data } = await api.delete('/users/prefs');
    return data;
  },
};
