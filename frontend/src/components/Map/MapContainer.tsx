import React, { useEffect, useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet';
import { LatLng } from 'leaflet';
// import { GMULayer } from './GMULayer';
import { SightingClusters } from './SightingClusters';
import { SightingHeatmap } from './SightingHeatmap';
import { useStore } from '@/store/store';
import { sightingsService } from '@/services/sightings';
import 'leaflet/dist/leaflet.css';

export const MapContainer: React.FC = () => {
  const { 
    filters, 
    currentPage, 
    setSightings, 
    setLoading, 
    setError,
    mapVisualization,
    sightings 
  } = useStore();
  
  const [center] = useState<LatLng>(new LatLng(39.5501, -105.7821)); // Colorado center
  const [zoom] = useState(7);

  useEffect(() => {
    const fetchSightings = async () => {
      // Don't set loading to true - it blocks the entire app
      setError(null);
      
      try {
        // Fetch sightings using the service with filters
        const response = await sightingsService.getSightings(filters, 1, 500);
        console.log('Map sightings API response:', response);
        
        // Filter to only show sightings with coordinates
        const sightingsWithCoords = response.items.filter(s => 
          (s.location?.lat && s.location?.lon) || (s.lat && s.lon)
        );
        
        console.log(`Loaded ${sightingsWithCoords.length} sightings with coordinates (out of ${response.items.length} total)`);
        setSightings(sightingsWithCoords, sightingsWithCoords.length);
      } catch (error) {
        console.error('Failed to fetch map sightings:', error);
        setError('Failed to load sightings. Please refresh the page.');
        setSightings([], 0);
      }
    };

    fetchSightings();
  }, [filters, currentPage, setSightings, setError]);

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
      
      {/* <GMULayer /> */}
      {mapVisualization === 'markers' ? (
        <SightingClusters />
      ) : (
        <SightingHeatmap sightings={sightings} visible={true} />
      )}
    </LeafletMap>
  );
};
