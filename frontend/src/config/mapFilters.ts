// Configuration for filtering out generic/placeholder coordinates from the map

interface LocationData {
  latitude: number;
  longitude: number;
  location_name?: string;
  location_accuracy_miles?: number;
  location_confidence_radius?: number;
}

// Generic GMU center coordinates that should be filtered out
const GENERIC_COORDINATES = [
  { lat: 39.5, lon: -105.0 },    // GMU 39 center
  { lat: 40.05, lon: -105.35 },  // GMU 29 center
  { lat: 39.5501, lon: -105.7821 }, // Colorado state center (Denver area)
  { lat: 39.0, lon: -105.5 },     // Generic Colorado center
  { lat: 39.75, lon: -104.99 },   // Another common generic point
];

// Default maximum radius (in miles) for locations to be shown on map
// Locations with accuracy worse than this are considered too generalized
const DEFAULT_MAX_LOCATION_RADIUS_MILES = 10;

// Check if coordinates match any generic GMU centers
export function shouldShowOnMap(location: LocationData, maxAccuracy?: number): boolean {
  if (!location.latitude || !location.longitude) {
    return false;
  }
  
  // Primary filter: Use location accuracy/radius if available
  const accuracyMiles = location.location_accuracy_miles || location.location_confidence_radius;
  const maxRadius = maxAccuracy || DEFAULT_MAX_LOCATION_RADIUS_MILES;
  
  if (accuracyMiles && accuracyMiles > maxRadius) {
    console.log(`Filtering out location with accuracy ${accuracyMiles} miles (> ${maxRadius})`);
    return false;
  }
  
  // Secondary filter: Check if coordinates match any known generic centers
  for (const generic of GENERIC_COORDINATES) {
    if (
      Math.abs(location.latitude - generic.lat) < 0.001 &&
      Math.abs(location.longitude - generic.lon) < 0.001
    ) {
      console.log(`Filtering out generic coordinate: ${location.latitude}, ${location.longitude}`);
      return false;
    }
  }
  
  return true;
}