import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import { useStore } from '../../store/store';
import { Sighting } from '../../types';

// Custom icon for wildlife sightings
const createSightingIcon = (species: string) => {
  const iconColors: { [key: string]: string } = {
    'elk': '#10b981',
    'deer': '#3b82f6',
    'bear': '#ef4444',
    'moose': '#8b5cf6',
    'mountain lion': '#f59e0b',
    'default': '#6b7280'
  };

  const color = iconColors[species.toLowerCase()] || iconColors.default;

  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; 
           display: flex; align-items: center; justify-content: center; color: white; 
           font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
           ${species.charAt(0).toUpperCase()}
           </div>`,
    className: 'custom-sighting-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  });
};

export const SightingClusters: React.FC = () => {
  const map = useMap();
  const sightings = useStore((state) => state.sightings);

  useEffect(() => {
    // Create marker cluster group
    const markers = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: true,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 80,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        let size = 'small';
        let className = 'marker-cluster-small';
        
        if (count > 50) {
          size = 'large';
          className = 'marker-cluster-large';
        } else if (count > 10) {
          size = 'medium';
          className = 'marker-cluster-medium';
        }
        
        return L.divIcon({
          html: `<div><span>${count}</span></div>`,
          className: `marker-cluster ${className}`,
          iconSize: L.point(40, 40)
        });
      }
    });

    // Add individual markers for each sighting
    sightings.forEach((sighting: Sighting) => {
      if (sighting.location?.lat && sighting.location?.lon) {
        const marker = L.marker([sighting.location.lat, sighting.location.lon], {
          icon: createSightingIcon(sighting.species || 'Wildlife')
        });

        // Create popup content
        const popupContent = `
          <div class="sighting-popup">
            <h3 class="font-bold text-lg mb-2">${sighting.species || 'Wildlife Sighting'}</h3>
            <p class="text-sm text-gray-600 mb-1">
              <strong>Date:</strong> ${sighting.sighting_date ? new Date(sighting.sighting_date).toLocaleDateString() : 'Unknown'}
            </p>
            ${sighting.raw_text ? `
              <p class="text-sm text-gray-600 mb-1">
                <strong>Description:</strong> ${sighting.raw_text}
              </p>
            ` : ''}
            ${sighting.source_type ? `
              <p class="text-sm text-gray-600 mb-1">
                <strong>Source:</strong> ${sighting.source_type}
              </p>
            ` : ''}
            ${sighting.gmu_unit ? `
              <p class="text-sm text-gray-600">
                <strong>GMU:</strong> ${sighting.gmu_unit}
              </p>
            ` : ''}
          </div>
        `;

        marker.bindPopup(popupContent, {
          maxWidth: 300,
          className: 'custom-popup'
        });

        markers.addLayer(marker);
      }
    });

    // Add cluster group to map
    map.addLayer(markers);

    // Cleanup function
    return () => {
      map.removeLayer(markers);
    };
  }, [map, sightings]);

  return null; // This component doesn't render anything directly
};
