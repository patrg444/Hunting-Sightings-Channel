// Wildlife Sighting types
export interface Sighting {
  id: string;
  species: string;
  raw_text: string;
  keyword_matched?: string;
  source_url: string;
  source_type: string;
  extracted_at: string;
  trail_name?: string;
  sighting_date?: string;
  gmu_unit?: number;
  location?: {
    lat: number;
    lon: number;
  };
  confidence_score?: number;
  reddit_post_title?: string;
  subreddit?: string;
  created_at: string;
  distance_miles?: number;
  date?: string;
  gmu?: number;
  source?: string;
  location_name?: string;
  matched_location?: string;
  gmu_notes?: string;
  description?: string;
  elevation?: number;
  location_accuracy_miles?: number;
  location_confidence_radius?: number;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
}

export interface SightingStats {
  total_count: number;
  species_counts: Record<string, number>;
  gmu_counts: Record<string, number>;
  source_counts: Record<string, number>;
}

// GMU types
export interface GMU {
  id: number;
  name: string;
  geometry: any; // GeoJSON geometry
}

// User types
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface UserPreferences {
  id: string;
  user_id: string;
  email_notifications: boolean;
  notification_time: string;
  gmu_filter: number[];
  species_filter: string[];
  created_at: string;
  updated_at: string;
}

// Filter types
export interface Filters {
  gmu?: number;
  gmuList?: number[];  // For multiple GMUs
  species?: string;
  speciesList?: string[];  // For multiple species
  source?: string;
  sourceList?: string[];  // For multiple sources
  startDate?: Date;
  endDate?: Date;
  lat?: number;
  lon?: number;
  radiusMiles?: number;
  excludeNoGmu?: boolean;  // Filter out entries without GMU
  maxLocationAccuracy?: number;  // Maximum location accuracy in miles
  enableAccuracyFilter?: boolean;  // Enable/disable accuracy filtering
  sourceType?: string;  // Alternative to source
  sourceTypes?: string[];  // Alternative to sourceList
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  size: number;
}

// Map types
export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {
  confirmPassword: string;
}

export interface AuthError {
  message: string;
  code?: string;
}
