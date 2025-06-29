import { supabase } from './auth';
import type { Filters, Sighting } from '@/types';
import { decodePostGISPoint } from '@/utils/postgis';

export const supabaseSightingsService = {
  async getSightings(filters: Filters) {
    try {
      let query = supabase
        .from('sightings')
        .select('*', { count: 'exact' });

      // Apply filters
      if (filters.gmu) {
        query = query.eq('gmu_unit', filters.gmu);
      }

      if (filters.species) {
        if (Array.isArray(filters.species)) {
          query = query.in('species', filters.species.map(s => s.toLowerCase()));
        } else {
          query = query.ilike('species', `%${filters.species}%`);
        }
      }

      if (filters.startDate) {
        const dateStr = typeof filters.startDate === 'string' 
          ? filters.startDate 
          : filters.startDate.toISOString().split('T')[0];
        query = query.gte('sighting_date', dateStr);
      }

      if (filters.endDate) {
        const dateStr = typeof filters.endDate === 'string'
          ? filters.endDate
          : filters.endDate.toISOString().split('T')[0];
        query = query.lte('sighting_date', dateStr);
      }

      // Order by date descending and limit
      query = query.order('sighting_date', { ascending: false }).limit(500);

      const { data, error, count } = await query;

      if (error) {
        console.error('Supabase query error:', error);
        throw error;
      }

      // Transform the data to match frontend format
      const sightings: Sighting[] = (data || []).map(s => {
        // Decode PostGIS location if present
        const coords = s.location ? decodePostGISPoint(s.location) : null;
        
        // Include all locations regardless of accuracy
        const locationAccuracy = s.location_accuracy_miles;
        
        return {
          id: s.id,
          species: s.species,
          location: coords ? {
            lat: coords.lat,
            lon: coords.lon,
            name: s.location_name || 'Unknown location'
          } : undefined,
          date: s.sighting_date,
          sighting_date: s.sighting_date,
          source: s.source_type,
          source_type: s.source_type,
          source_url: s.source_url,
          description: s.raw_text || '',
          raw_text: s.raw_text || '',
          gmu: s.gmu_unit,
          gmu_unit: s.gmu_unit,
          confidence_score: s.confidence_score || 0.5,
          created_at: s.created_at,
          extracted_at: s.extracted_at,
          location_name: s.location_name,
          location_accuracy_miles: locationAccuracy
        };
      });

      return {
        sightings,
        total: count || sightings.length
      };
    } catch (error) {
      console.error('Error fetching sightings from Supabase:', error);
      throw error;
    }
  }
};