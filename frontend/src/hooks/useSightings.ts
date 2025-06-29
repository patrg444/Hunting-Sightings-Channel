import { useEffect } from 'react';
import { useStore } from '@/store/store';
import { sightingsService } from '@/services/sightings';

export const useSightings = () => {
  const { 
    filters, 
    currentPage, 
    viewMode,
    setSightings, 
    setLoading, 
    setError 
  } = useStore();

  useEffect(() => {
    // Only fetch sightings when in table view
    if (viewMode !== 'table') {
      return;
    }
    
    const fetchSightings = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await sightingsService.getSightings(filters, currentPage, 100);
        setSightings(response.items, response.total);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch sightings');
        setSightings([], 0);
      } finally {
        setLoading(false);
      }
    };

    fetchSightings();
  }, [filters, currentPage, viewMode, setSightings, setLoading, setError]);
};