// Configuration for filtering out generic/placeholder coordinates from the map

interface LocationData {
  latitude: number;
  longitude: number;
  location_name?: string;
  location_accuracy_miles?: number;
  location_confidence_radius?: number;
}

// Default maximum radius (in miles) for locations to be shown on map
// Locations with accuracy worse than this are considered too generalized
const DEFAULT_MAX_LOCATION_RADIUS_MILES = 10;

// Check if location should be shown on map based on user-controlled accuracy filter
export function shouldShowOnMap(location: LocationData, maxAccuracy?: number): boolean {
  if (!location.latitude || !location.longitude) {
    return false;
  }
  
  // Use location accuracy/radius if available
  const accuracyMiles = location.location_accuracy_miles || location.location_confidence_radius;
  const maxRadius = maxAccuracy || DEFAULT_MAX_LOCATION_RADIUS_MILES;
  
  // Only filter based on user-controlled accuracy setting
  if (accuracyMiles && accuracyMiles > maxRadius) {
    console.log(`Filtering out location with accuracy ${accuracyMiles} miles (> ${maxRadius})`);
    return false;
  }
  
  return true;
}