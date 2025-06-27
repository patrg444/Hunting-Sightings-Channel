/**
 * Utility to decode PostGIS WKB (Well-Known Binary) format
 * PostGIS stores geography as hex-encoded WKB
 */

export interface Coordinates {
  lat: number;
  lon: number;
}

/**
 * Decode PostGIS WKB hex string to coordinates
 * Example input: "0101000020E6100000E78C28ED0D725AC0CAC342AD69C64340"
 */
export function decodePostGISPoint(wkbHex: string): Coordinates | null {
  if (!wkbHex || typeof wkbHex !== 'string') {
    return null;
  }

  try {
    // WKB format for POINT with SRID 4326:
    // Byte 0: Endianness (01 = little-endian)
    // Bytes 1-4: Geometry type (01000000 = POINT)
    // Bytes 5-8: SRID (E6100000 = 4326 in little-endian)
    // Bytes 9-16: X coordinate (longitude) as double
    // Bytes 17-24: Y coordinate (latitude) as double
    
    // Skip the header (18 hex chars = 9 bytes)
    const coordsHex = wkbHex.substring(18);
    
    // Extract X (longitude) - 16 hex chars = 8 bytes
    const lonHex = coordsHex.substring(0, 16);
    const lon = hexToDouble(lonHex);
    
    // Extract Y (latitude) - 16 hex chars = 8 bytes
    const latHex = coordsHex.substring(16, 32);
    const lat = hexToDouble(latHex);
    
    // Validate coordinates
    if (isNaN(lat) || isNaN(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      return null;
    }
    
    return { lat, lon };
  } catch (error) {
    console.error('Error decoding PostGIS point:', error);
    return null;
  }
}

/**
 * Convert little-endian hex string to double
 */
function hexToDouble(hex: string): number {
  // Convert hex pairs to bytes in reverse order (little-endian)
  const bytes = [];
  for (let i = 0; i < 16; i += 2) {
    bytes.push(parseInt(hex.substr(i, 2), 16));
  }
  
  // Create ArrayBuffer and DataView
  const buffer = new ArrayBuffer(8);
  const view = new DataView(buffer);
  
  // Set bytes in little-endian order
  for (let i = 0; i < 8; i++) {
    view.setUint8(i, bytes[i]);
  }
  
  // Read as little-endian double
  return view.getFloat64(0, true);
}