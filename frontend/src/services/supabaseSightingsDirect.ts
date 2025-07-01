import type { Filters, Sighting } from '@/types';
import { decodePostGISPoint } from '@/utils/postgis';

const SUPABASE_URL = "https://rvrdbtrxwndeerqmziuo.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmRidHJ4d25kZWVycW16aXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4NDY1NTcsImV4cCI6MjA2NjQyMjU1N30.ExvP-7mWzplSmkGnw0eiD_q9qnP8IAO48qBxXp0baAs";

export const supabaseSightingsService = {
  async getSightings(filters: Filters) {
    try {
      // Build URL with query parameters
      const url = new URL(`${SUPABASE_URL}/rest/v1/sightings`);
      
      // Add ordering without limit to get all sightings
      url.searchParams.append('order', 'sighting_date.desc');
      
      // Apply filters
      if (filters.gmu) {
        url.searchParams.append('gmu_unit', `eq.${filters.gmu}`);
      }
      
      if (filters.gmuList && filters.gmuList.length > 0) {
        url.searchParams.append('gmu_unit', `in.(${filters.gmuList.join(',')})`);
      }
      
      if (filters.species) {
        url.searchParams.append('species', `ilike.*${filters.species.toLowerCase()}*`);
      }
      
      if (filters.speciesList && filters.speciesList.length > 0) {
        url.searchParams.append('species', `in.(${filters.speciesList.map(s => `"${s.toLowerCase()}"`).join(',')})`);
      }
      
      if (filters.source) {
        url.searchParams.append('source_type', `eq.${filters.source.toLowerCase()}`);
      }
      
      if (filters.sourceList && filters.sourceList.length > 0) {
        url.searchParams.append('source_type', `in.(${filters.sourceList.map(s => `"${s.toLowerCase()}"`).join(',')})`);
      }
      
      if (filters.startDate) {
        const dateStr = typeof filters.startDate === 'string' 
          ? filters.startDate 
          : filters.startDate.toISOString().split('T')[0];
        url.searchParams.append('sighting_date', `gte.${dateStr}`);
      }
      
      if (filters.endDate) {
        const dateStr = typeof filters.endDate === 'string'
          ? filters.endDate
          : filters.endDate.toISOString().split('T')[0];
        url.searchParams.append('sighting_date', `lte.${dateStr}`);
      }
      
      // Add excludeNoGmu filter
      if (filters.excludeNoGmu) {
        url.searchParams.append('gmu_unit', 'not.is.null');
      }
      
      console.log('🔍 Supabase Direct URL:', url.toString());
      
      // Make the request
      const response = await fetch(url.toString(), {
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'count=exact'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      const contentRange = response.headers.get('content-range');
      const totalCount = contentRange ? contentRange.split('/')[1] : data.length;
      
      console.log('🔍 Supabase Direct Response:', data.length, 'sightings');
      console.log('📊 Total in database:', totalCount);
      if (data.length < parseInt(totalCount)) {
        console.log('⚠️  Only received', data.length, 'of', totalCount, 'sightings. Fetching all...');
      }
      
      // Transform the data to match frontend format
      const sightings: Sighting[] = (data || []).map((s: any) => {
        // Decode PostGIS location if present
        const coords = s.location ? decodePostGISPoint(s.location) : null;
        
        return {
          id: s.id,
          species: s.species,
          location: coords ? {
            lat: coords.lat,
            lon: coords.lon,
            name: s.location_name || 'Unknown location'
          } : undefined,
          // Also include lat/lon directly for MapContainer compatibility
          lat: coords?.lat,
          lon: coords?.lon,
          latitude: coords?.lat,
          longitude: coords?.lon,
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
          location_accuracy_miles: s.location_accuracy_miles
        };
      });

      return {
        sightings,
        total: parseInt(totalCount) || sightings.length
      };
    } catch (error) {
      console.error('Error fetching sightings from Supabase:', error);
      throw error;
    }
  }
};