import React, { useEffect, useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { GMULayer } from './GMULayer';
import { SightingClusters } from './SightingClusters';
import { useStore } from '@/store/store';
import { sightingsAuthService } from '@/services/sightingsAuth';
import 'leaflet/dist/leaflet.css';

export const MapContainer: React.FC = () => {
  const { 
    filters, 
    currentPage, 
    setSightings, 
    setLoading, 
    setError 
  } = useStore();
  
  const [center] = useState<LatLng>(new LatLng(39.5501, -105.7821)); // Colorado center
  const [zoom] = useState(7);

  useEffect(() => {
    const fetchSightings = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Clear existing sightings first
        setSightings([], 0);
        
        // Apply date filter for free users (5 days)
        let effectiveFilters = { ...filters };
        const user = useStore.getState().user;
        
        // For now, default to 5-day filter for all users since subscription model isn't loaded
        const fiveDaysAgo = new Date();
        fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);
        
        effectiveFilters = {
          ...filters,
          startDate: fiveDaysAgo.toISOString().split('T')[0],
        };
        
        const response = await sightingsAuthService.getSightings(effectiveFilters);
        console.log(`Loaded ${response.sightings.length} sightings with 5-day filter`);
        setSightings(response.sightings, response.total);
      } catch (error) {
        console.error('Failed to fetch sightings:', error);
        setError('Failed to load sightings');
        setSightings([], 0);
      } finally {
        setLoading(false);
      }
    };

    fetchSightings();
  }, [filters, currentPage, setSightings, setLoading, setError]);

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
      
      <GMULayer />
      <SightingClusters />
    </LeafletMap>
  );
};
