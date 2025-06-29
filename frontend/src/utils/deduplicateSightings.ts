/**
 * Utility to deduplicate sightings based on content similarity
 */

import { Sighting } from '@/types';

interface DuplicateGroup {
  key: string;
  sightings: Sighting[];
  keepIndex: number; // Index of the sighting to keep
}

/**
 * Generate a key for deduplication based on sighting content
 */
function generateDedupeKey(sighting: Sighting): string {
  const species = (sighting.species || '').toLowerCase().trim();
  const date = sighting.sighting_date || sighting.date || '';
  const source = (sighting.source_type || sighting.source || '').toLowerCase().trim();
  const text = (sighting.raw_text || sighting.description || '').slice(0, 100).trim();
  const location = (sighting.location_name || '').trim();
  
  return `${species}|${date}|${source}|${text}|${location}`;
}

/**
 * Deduplicate an array of sightings
 * @param sightings Array of sightings to deduplicate
 * @returns Deduplicated array of sightings
 */
export function deduplicateSightings(sightings: Sighting[]): Sighting[] {
  // Group sightings by deduplication key
  const groups = new Map<string, Sighting[]>();
  
  sightings.forEach(sighting => {
    const key = generateDedupeKey(sighting);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(sighting);
  });
  
  // For each group, keep only one sighting (preferably the one with coordinates)
  const deduplicated: Sighting[] = [];
  
  groups.forEach((group, key) => {
    if (group.length === 1) {
      // No duplicates
      deduplicated.push(group[0]);
    } else {
      // Multiple sightings with same key - pick the best one
      // Prefer: 1) Has coordinates, 2) Has GMU, 3) Oldest (first in array)
      const best = group.reduce((prev, current) => {
        // Check if current has coordinates
        const prevHasCoords = (prev.location?.lat && prev.location?.lon) || 
                             (prev.lat && prev.lon);
        const currentHasCoords = (current.location?.lat && current.location?.lon) || 
                                (current.lat && current.lon);
        
        if (currentHasCoords && !prevHasCoords) {
          return current;
        }
        if (prevHasCoords && !currentHasCoords) {
          return prev;
        }
        
        // Both have or don't have coords, check GMU
        const prevHasGmu = prev.gmu_unit || prev.gmu;
        const currentHasGmu = current.gmu_unit || current.gmu;
        
        if (currentHasGmu && !prevHasGmu) {
          return current;
        }
        
        // Keep the first one (oldest)
        return prev;
      });
      
      deduplicated.push(best);
      
      // Log duplicates for debugging
      if (process.env.NODE_ENV === 'development') {
        console.log(`Found ${group.length} duplicates for:`, {
          species: best.species,
          date: best.sighting_date || best.date,
          source: best.source_type || best.source,
          location: best.location_name,
          text: (best.raw_text || best.description || '').slice(0, 50) + '...'
        });
      }
    }
  });
  
  return deduplicated;
}

/**
 * Get duplicate statistics for an array of sightings
 */
export function getDuplicateStats(sightings: Sighting[]): {
  totalSightings: number;
  uniqueSightings: number;
  duplicateCount: number;
  duplicateGroups: number;
} {
  const groups = new Map<string, number>();
  
  sightings.forEach(sighting => {
    const key = generateDedupeKey(sighting);
    groups.set(key, (groups.get(key) || 0) + 1);
  });
  
  let duplicateCount = 0;
  let duplicateGroups = 0;
  
  groups.forEach(count => {
    if (count > 1) {
      duplicateGroups++;
      duplicateCount += count - 1; // Extra copies
    }
  });
  
  return {
    totalSightings: sightings.length,
    uniqueSightings: sightings.length - duplicateCount,
    duplicateCount,
    duplicateGroups
  };
}