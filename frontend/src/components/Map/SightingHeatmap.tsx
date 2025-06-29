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

    sightings.forEach(sighting => {
      const lat = sighting.location?.lat || sighting.lat;
      const lon = sighting.location?.lon || sighting.lon;
      
      if (lat && lon) {
        const radius = getRadiusFromSighting(sighting);
        
        // Intensity calculation:
        // - Very precise (< 0.5 mile): intensity 1.0
        // - Precise (0.5-2 miles): intensity 0.8-1.0
        // - Good (2-5 miles): intensity 0.6-0.8
        // - Moderate (5-15 miles): intensity 0.4-0.6
        // - Low confidence (15-30 miles): intensity 0.2-0.4
        // - Very low (> 30 miles): intensity 0.1-0.2
        let intensity = 1.0;
        if (radius < 0.5) {
          intensity = 1.0;
        } else if (radius < 2) {
          intensity = 0.8 + (2 - radius) * 0.133; // 0.8 to 1.0
        } else if (radius < 5) {
          intensity = 0.6 + (5 - radius) * 0.067; // 0.6 to 0.8
        } else if (radius < 15) {
          intensity = 0.4 + (15 - radius) * 0.02; // 0.4 to 0.6
        } else if (radius < 30) {
          intensity = 0.2 + (30 - radius) * 0.013; // 0.2 to 0.4
        } else {
          intensity = Math.max(0.1, 0.2 - (radius - 30) * 0.002); // 0.1 to 0.2
        }

        heatData.push([lat, lon, intensity]);
      }
    });

    // Calculate initial radius based on zoom
    const getRadiusForZoom = (zoom: number) => {
      if (zoom < 8) return 20;
      if (zoom < 10) return 25;
      if (zoom < 12) return 30;
      return 35;
    };

    // Create heat layer with custom options
    const heatLayer = L.heatLayer(heatData, {
      radius: getRadiusForZoom(map.getZoom()),
      blur: 20,   // Amount of blur
      maxZoom: 10, // Zoom level where points reach maximum intensity
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

    // Update radius on zoom
    const updateRadius = () => {
      const newRadius = getRadiusForZoom(map.getZoom());
      heatLayer.setOptions({ radius: newRadius });
    };

    map.on('zoomend', updateRadius);

    // Cleanup
    return () => {
      map.off('zoomend', updateRadius);
      map.removeLayer(heatLayer);
    };
  }, [map, sightings, visible]);

  return null;
};