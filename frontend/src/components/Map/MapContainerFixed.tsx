import React, { useEffect, useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { SightingClusters } from './SightingClusters';
import { useStore } from '@/store/store';
import 'leaflet/dist/leaflet.css';

export const MapContainer: React.FC = () => {
  const { setSightings, setError } = useStore();
  const [center] = useState<LatLng>(new LatLng(39.5501, -105.7821)); // Colorado center
  const [zoom] = useState(7);

  useEffect(() => {
    const fetchSightings = async () => {
      setError(null);
      
      try {
        // Fetch sightings with coordinates directly
        const response = await fetch('http://localhost:8002/api/v1/sightings/with-coords');
        const data = await response.json();
        
        console.log('Map data loaded:', {
          total: data.total,
          sightings: data.sightings.length,
          firstSighting: data.sightings[0]
        });
        
        // Set sightings in store
        setSightings(data.sightings, data.total);
      } catch (error) {
        console.error('Failed to fetch map sightings:', error);
        setError('Failed to load map data. Please refresh the page.');
        setSightings([], 0);
      }
    };

    fetchSightings();
  }, [setSightings, setError]);

  return (
    <LeafletMap
      center={center}
      zoom={zoom}
      className="w-full h-full"
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <ZoomControl position="topright" />
      <SightingClusters />
    </LeafletMap>
  );
};