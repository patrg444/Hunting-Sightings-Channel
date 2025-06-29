import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat/dist/leaflet-heat.js';
import { Sighting } from '../../types';
import { shouldShowOnMap } from '../../config/mapFilters';

// Extend Leaflet types for the heat layer
declare module 'leaflet' {
  function heatLayer(latlngs: Array<[number, number, number]>, options?: any): any;
}

interface SightingHeatmapProps {
  sightings: Sighting[];
  visible: boolean;
}

// Helper to get actual radius value from sighting
function getRadiusFromSighting(sighting: Sighting): number {
  return sighting.location_confidence_radius || 
         sighting.location_accuracy_miles || 
         10; // Default 10 miles if no radius specified
}

export const SightingHeatmap: React.FC<SightingHeatmapProps> = ({ sightings, visible }) => {
  const map = useMap();

  useEffect(() => {
    if (!visible || sightings.length === 0) return;

    // Convert sightings to heat map data points
    // Format: [lat, lng, intensity]
    const heatData: Array<[number, number, number]> = [];
    
    // Count sightings at each location
    const locationCounts = new Map<string, { lat: number; lon: number; count: number }>();
    
    sightings.forEach(sighting => {
      const lat = sighting.location?.lat || sighting.lat;
      const lon = sighting.location?.lon || sighting.lon;
      
      // Filter out generalized locations
      if (lat && lon && shouldShowOnMap({
        latitude: lat,
        longitude: lon,
        location_name: sighting.location_name,
        location_accuracy_miles: sighting.location_accuracy_miles,
        location_confidence_radius: sighting.location_confidence_radius
      })) {
        // Round to ~100m precision to group nearby sightings
        const locationKey = `${lat.toFixed(3)},${lon.toFixed(3)}`;
        
        if (!locationCounts.has(locationKey)) {
          locationCounts.set(locationKey, { lat, lon, count: 0 });
        }
        locationCounts.get(locationKey)!.count++;
      }
    });
    
    // Find the maximum count for normalization
    const counts = Array.from(locationCounts.values()).map(loc => loc.count);
    const maxCount = Math.max(...counts);
    const minCount = Math.min(...counts);
    
    // Create heat data with normalized intensities
    locationCounts.forEach(location => {
      // Normalize count to 0-1 range
      let intensity;
      if (maxCount === minCount) {
        // All locations have same count
        intensity = 0.8;
      } else {
        // Scale from 0.2 to 1.0 based on count
        intensity = 0.2 + (0.8 * ((location.count - minCount) / (maxCount - minCount)));
      }
      
      // Add point for each sighting at this location to create proper density
      // This makes the heat map additive at each location but normalized across locations
      for (let i = 0; i < location.count; i++) {
        heatData.push([location.lat, location.lon, intensity]);
      }
    });

    // Fixed radius that doesn't change with zoom
    const FIXED_RADIUS = 35;

    // Check if heatLayer function exists
    if (!L.heatLayer) {
      console.error('Leaflet.heat plugin not loaded!');
      return;
    }
    
    // Create heat layer with custom options
    const heatLayer = L.heatLayer(heatData, {
      radius: FIXED_RADIUS,
      blur: 25,   // More blur for smoother appearance
      maxZoom: 18, // Higher value to maintain consistency across zoom levels
      gradient: {
        0.0: 'transparent',
        0.2: 'rgba(0, 0, 255, 0.5)',     // Blue (low confidence)
        0.4: 'rgba(0, 255, 255, 0.6)',   // Cyan
        0.6: 'rgba(0, 255, 0, 0.7)',     // Green (moderate confidence)
        0.8: 'rgba(255, 255, 0, 0.8)',   // Yellow
        1.0: 'rgba(255, 0, 0, 0.9)'      // Red (high confidence)
      },
    });

    // Add to map
    heatLayer.addTo(map);

    // No zoom updates needed - keeping consistent radius

    // Cleanup
    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, sightings, visible]);

  return null;
};