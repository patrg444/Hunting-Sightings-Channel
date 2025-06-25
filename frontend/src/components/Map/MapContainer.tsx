import React, { useEffect, useState } from 'react';
import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { GMULayer } from './GMULayer';
import { SightingClusters } from './SightingClusters';
import { useStore } from '@/store/store';
import { wildlifeService } from '@/services/wildlife';
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
      // Don't set loading to true - it blocks the entire app
      setError(null);
      
      try {
        // Apply date filter for free users (5 days)
        let effectiveFilters = { ...filters };
        const fiveDaysAgo = new Date();
        fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);
        
        effectiveFilters = {
          ...filters,
          startDate: fiveDaysAgo.toISOString().split('T')[0],
        };
        
        // Use wildlife service which we know works
        const response = await wildlifeService.getWildlifeSightings(effectiveFilters);
        console.log('Wildlife API response:', response);
        
        // Transform sightings - filter to last 5 days on frontend too
        const transformedSightings = response.sightings
          .filter(s => {
            if (!s.date && !s.sighting_date && !s.created_at) return false;
            const sightingDate = new Date(s.date || s.sighting_date || s.created_at);
            return sightingDate >= new Date(fiveDaysAgo);
          })
          .map(s => wildlifeService.transformSighting(s))
          .filter(s => s !== null);
        
        console.log(`Loaded ${transformedSightings.length} sightings (filtered to last 5 days)`);
        setSightings(transformedSightings, transformedSightings.length);
      } catch (error) {
        console.error('Failed to fetch sightings:', error);
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
      
      <GMULayer />
      <SightingClusters />
    </LeafletMap>
  );
};
