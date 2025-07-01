// Known generic/placeholder coordinates that should have their radius overridden
// These are commonly assigned by LLM validators when exact location is unknown

export interface GenericCoordinate {
  lat: number;
  lon: number;
  tolerance: number; // degrees tolerance for matching
  description: string;
  overrideRadiusMiles: number; // radius to assign to these coordinates
}

export const GENERIC_COLORADO_COORDINATES: GenericCoordinate[] = [
  // Colorado geographic centers - all get 150 mile radius
  { lat: 39.5501, lon: -105.7821, tolerance: 0.01, description: "Colorado Geographic Center", overrideRadiusMiles: 150 },
  { lat: 39.0000, lon: -105.5000, tolerance: 0.01, description: "Rounded Colorado Center", overrideRadiusMiles: 150 },
  { lat: 39.7392, lon: -104.9903, tolerance: 0.01, description: "Denver Center", overrideRadiusMiles: 150 },
  { lat: 39.1131, lon: -105.3580, tolerance: 0.01, description: "Colorado Geometric Center", overrideRadiusMiles: 150 },
  { lat: 39.0, lon: -105.0, tolerance: 0.01, description: "Very Rounded Center", overrideRadiusMiles: 150 },
  { lat: 39.72, lon: -105.7, tolerance: 0.01, description: "Generic Colorado Location", overrideRadiusMiles: 150 },
  
  // Add more as discovered from the coordinate analysis
];

/**
 * Get the override radius for a coordinate if it matches a generic location
 */
export function getOverrideRadius(lat: number, lon: number): number | null {
  const match = GENERIC_COLORADO_COORDINATES.find(generic => {
    const latDiff = Math.abs(lat - generic.lat);
    const lonDiff = Math.abs(lon - generic.lon);
    return latDiff <= generic.tolerance && lonDiff <= generic.tolerance;
  });
  
  return match ? match.overrideRadiusMiles : null;
}

/**
 * Check if a coordinate pair matches any generic coordinates
 */
export function isGenericCoordinate(lat: number, lon: number): boolean {
  return GENERIC_COLORADO_COORDINATES.some(generic => {
    const latDiff = Math.abs(lat - generic.lat);
    const lonDiff = Math.abs(lon - generic.lon);
    return latDiff <= generic.tolerance && lonDiff <= generic.tolerance;
  });
}