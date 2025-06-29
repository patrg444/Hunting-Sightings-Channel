import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat/dist/leaflet-heat.js';
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
    
    // First pass: collect all data points with their raw scores
    interface HeatPoint {
      lat: number;
      lon: number;
      radius: number;
      score: number; // Combined score from radius and density
    }
    
    const points: HeatPoint[] = [];
    const locationGroups = new Map<string, HeatPoint[]>();
    
    // Collect all points and group by location
    sightings.forEach(sighting => {
      const lat = sighting.location?.lat || sighting.lat;
      const lon = sighting.location?.lon || sighting.lon;
      
      if (lat && lon) {
        const radius = getRadiusFromSighting(sighting);
        const locationKey = `${lat.toFixed(3)},${lon.toFixed(3)}`;
        
        // Base score inversely related to radius (smaller radius = higher confidence = higher score)
        const radiusScore = Math.max(0, 1 - (radius / 50)); // Normalize radius to 0-1 scale
        
        const point: HeatPoint = { lat, lon, radius, score: radiusScore };
        points.push(point);
        
        if (!locationGroups.has(locationKey)) {
          locationGroups.set(locationKey, []);
        }
        locationGroups.get(locationKey)!.push(point);
      }
    });
    
    // Calculate density scores
    points.forEach(point => {
      const locationKey = `${point.lat.toFixed(3)},${point.lon.toFixed(3)}`;
      const groupSize = locationGroups.get(locationKey)?.length || 1;
      // Add density bonus to score
      point.score = point.score + (groupSize - 1) * 0.1; // Each additional sighting adds 0.1 to score
    });
    
    // Find min and max scores for normalization
    const scores = points.map(p => p.score);
    const minScore = Math.min(...scores);
    const maxScore = Math.max(...scores);
    const scoreRange = maxScore - minScore || 1; // Avoid division by zero
    
    // Normalize all scores to 0-1 range and create heat data
    points.forEach(point => {
      // Normalize to ensure we use the full color gradient
      const normalizedIntensity = (point.score - minScore) / scoreRange;
      // Ensure minimum visibility even for lowest scores
      const intensity = 0.1 + (normalizedIntensity * 0.9);
      heatData.push([point.lat, point.lon, intensity]);
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