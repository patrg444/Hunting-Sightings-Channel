import api from './api';
import type { Sighting, Filters } from '@/types';
import { shouldShowOnMap } from '@/config/mapFilters';

// Sightings API service with authentication and proper filtering
export const sightingsAuthService = {
  // Get sightings with authentication-based filtering
  async getSightings(filters: Filters): Promise<{ sightings: Sighting[], total: number }> {
    const params = new URLSearchParams();
    
    console.log('SightingsAuth filters:', filters);
    
    // Handle GMU filters
    if (filters.gmu) {
      params.append('gmu', filters.gmu.toString());
    }
    
    // Handle species filters (convert array to individual params)
    if (filters.species && filters.species.length > 0) {
      filters.species.forEach(s => params.append('species', s));
    }
    
    // Handle source filters
    if (filters.sourceTypes && filters.sourceTypes.length > 0) {
      filters.sourceTypes.forEach(s => params.append('source_type', s));
    } else if (filters.sourceType) {
      params.append('source_type', filters.sourceType);
    }
    
    // Handle date filters
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    
    // Pagination
    params.append('skip', '0');
    params.append('limit', '500');
    
    const url = `/api/v1/sightings?${params}`;
    console.log('SightingsAuth API URL:', url);
    
    try {
      const { data } = await api.get(url);
      console.log('API Response:', data);
      
      // Transform the response to match frontend format
      const transformedSightings = (data.items || [])
        .map((s: any) => transformSighting(s))
        .filter(s => s !== null);
      
      return {
        sightings: transformedSightings,
        total: data.total || transformedSightings.length
      };
    } catch (error) {
      console.error('Failed to fetch sightings:', error);
      // Return empty result instead of throwing
      return {
        sightings: [],
        total: 0
      };
    }
  }
};

// Transform backend sighting to frontend format
function transformSighting(sighting: any): Sighting | null {
  // Filter out generic GMU coordinates
  if (!shouldShowOnMap({
    latitude: sighting.latitude || sighting.location_lat,
    longitude: sighting.longitude || sighting.location_lon,
    location_name: sighting.location_name
  })) {
    return null;
  }
  
  const lat = sighting.latitude || sighting.location_lat;
  const lon = sighting.longitude || sighting.location_lon;
  
  // Must have valid coordinates
  if (!lat || !lon) {
    return null;
  }
  
  return {
    id: sighting.id?.toString() || Math.random().toString(),
    species: sighting.species,
    date: sighting.sighting_date,
    sighting_date: sighting.sighting_date,
    location: {
      lat: lat,
      lon: lon,
      name: sighting.location_name || 'Unknown'
    },
    location_name: sighting.location_name,
    gmu: sighting.gmu || sighting.gmu_unit,
    gmu_unit: sighting.gmu || sighting.gmu_unit,
    source: sighting.source_type,
    source_type: sighting.source_type,
    source_url: sighting.source_url,
    description: sighting.raw_text || sighting.description || '',
    confidence: sighting.confidence_score || 0.8,
    reported_by: sighting.reported_by || 'Anonymous',
    created_at: sighting.created_at,
    validated: sighting.validated,
    raw_text: sighting.raw_text,
    latitude: lat,
    longitude: lon
  };
}