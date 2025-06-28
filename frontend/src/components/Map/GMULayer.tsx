import React, { useEffect, useState } from 'react';
import { GeoJSON } from 'react-leaflet';
import { FeatureCollection } from 'geojson';
import L from 'leaflet';

export const GMULayer: React.FC = () => {
  const [gmuData, setGmuData] = useState<FeatureCollection | null>(null);

  useEffect(() => {
    // Verify this path points to your GeoJSON file in the `public` folder
    fetch('/data/gmu/colorado_gmu_simplified.geojson')
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => setGmuData(data))
      .catch(error => console.error('Failed to load GMU data:', error));
  }, []);

  // Converted `gmuStyle` from an object to a function for react-leaflet v3+
  const gmuStyle = () => {
    return {
      color: '#1e40af',
      weight: 2,
      opacity: 0.6,
      fillOpacity: 0.1,
      fillColor: '#3b82f6'
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    if (feature.properties && feature.properties.GMUID) {
      // Fixed the typo from `bindTooltip` to `bindTooltip`
      (layer as L.Path).bindTooltip(
        `GMU ${feature.properties.GMUID}`,
        { permanent: false, sticky: true }
      );
    }
  };

  if (!gmuData) {
    return null; // Don't render anything until data is loaded
  }

  return (
    <GeoJSON 
      data={gmuData} 
      style={gmuStyle}
      onEachFeature={onEachFeature}
    />
  );
};
