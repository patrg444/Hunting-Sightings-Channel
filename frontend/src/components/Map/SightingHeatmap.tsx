import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import { Sighting } from '../../types';

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
    
    // First pass: collect all data and find density hotspots
    const locationCounts = new Map<string, number>();
    
    sightings.forEach(sighting => {
      const lat = sighting.location?.lat || sighting.lat;
      const lon = sighting.location?.lon || sighting.lon;
      
      if (lat && lon) {
        // Create a key for nearby locations (round to ~1km precision)
        const key = `${lat.toFixed(2)},${lon.toFixed(2)}`;
        locationCounts.set(key, (locationCounts.get(key) || 0) + 1);
        
        const radius = getRadiusFromSighting(sighting);
        
        // Base intensity on confidence radius
        let baseIntensity = 1.0;
        if (radius < 0.5) {
          baseIntensity = 1.0;
        } else if (radius < 2) {
          baseIntensity = 0.8 + (2 - radius) * 0.133;
        } else if (radius < 5) {
          baseIntensity = 0.6 + (5 - radius) * 0.067;
        } else if (radius < 15) {
          baseIntensity = 0.4 + (15 - radius) * 0.02;
        } else if (radius < 30) {
          baseIntensity = 0.2 + (30 - radius) * 0.013;
        } else {
          baseIntensity = Math.max(0.1, 0.2 - (radius - 30) * 0.002);
        }

        heatData.push([lat, lon, baseIntensity]);
      }
    });
    
    // Find the maximum density for normalization
    const maxDensity = Math.max(...locationCounts.values());
    
    // Normalize intensities based on local density
    if (maxDensity > 1) {
      heatData.forEach((point, index) => {
        const key = `${point[0].toFixed(2)},${point[1].toFixed(2)}`;
        const density = locationCounts.get(key) || 1;
        // Boost intensity for high-density areas
        const densityBoost = 0.5 + (0.5 * (density / maxDensity));
        heatData[index][2] = Math.min(1.0, point[2] * densityBoost);
      });
    }

    // Fixed radius that doesn't change with zoom
    const FIXED_RADIUS = 25;

    // Create heat layer with custom options
    const heatLayer = L.heatLayer(heatData, {
      radius: FIXED_RADIUS,
      blur: 15,   // Amount of blur
      maxZoom: 14, // Higher value to maintain consistency across zoom levels
      max: 1.0,   // Maximum intensity
      gradient: {
        0.0: 'transparent',
        0.1: 'rgba(150, 200, 255, 0.3)',   // Very light blue (low confidence)
        0.3: 'rgba(100, 150, 255, 0.5)',   // Light blue
        0.5: 'rgba(50, 200, 100, 0.6)',    // Green (moderate confidence)
        0.7: 'rgba(255, 200, 50, 0.7)',    // Yellow-orange
        0.9: 'rgba(255, 100, 50, 0.8)',    // Orange (high confidence)
        1.0: 'rgba(255, 50, 50, 0.9)'      // Red (very high confidence)
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