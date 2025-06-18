import React, { useEffect, useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { GMULayer } from './GMULayer';
import { SightingClusters } from './SightingClusters';
import { useStore } from '@/store/store';
import { sightingsService } from '@/services/sightings';
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
        const response = await sightingsService.getSightings(filters, currentPage);
        setSightings(response.items, response.total);
      } catch (error) {
        console.error('Failed to fetch sightings:', error);
        setError('Failed to load sightings');
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
