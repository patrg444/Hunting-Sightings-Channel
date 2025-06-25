// Configuration for filtering out generic/placeholder coordinates from the map

interface LocationData {
  latitude: number;
  longitude: number;
  location_name?: string;
}

// Generic GMU center coordinates that should be filtered out
const GENERIC_COORDINATES = [
  { lat: 39.5, lon: -105.0 },    // GMU 39 center
  { lat: 40.05, lon: -105.35 },  // GMU 29 center
];

// Check if coordinates match any generic GMU centers
export function shouldShowOnMap(location: LocationData): boolean {
  if (!location.latitude || !location.longitude) {
    return false;
  }
  
  // Check if coordinates match any generic GMU centers
  for (const generic of GENERIC_COORDINATES) {
    if (
      Math.abs(location.latitude - generic.lat) < 0.001 &&
      Math.abs(location.longitude - generic.lon) < 0.001
    ) {
      console.log(`Filtering out generic coordinate: ${location.latitude}, ${location.longitude}`);
      return false;
    }
  }
  
  // Additional check for vague location names
  if (location.location_name) {
    const vagueName = location.location_name.toLowerCase();
    if (
      vagueName === 'colorado' ||
      vagueName === 'general' ||
      vagueName === 'unknown' ||
      vagueName === 'gmu' ||
      vagueName.includes('unit ')
    ) {
      console.log(`Filtering out vague location: ${location.location_name}`);
      return false;
    }
  }
  
  return true;
}