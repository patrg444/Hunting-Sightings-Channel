import { test, expect } from '@playwright/test';

test.describe('Map Loading Issue', () => {
  test('should load map markers from production', async ({ page }) => {
    // Test production site
    await page.goto('http://54.203.54.74/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if map container exists
    const mapContainer = page.locator('.leaflet-container');
    await expect(mapContainer).toBeVisible();
    
    // Wait for potential API calls
    await page.waitForTimeout(5000);
    
    // Check for map markers
    const markers = page.locator('.leaflet-marker-icon');
    const markerCount = await markers.count();
    console.log(`Found ${markerCount} markers on the map`);
    
    // Check for cluster markers
    const clusters = page.locator('.leaflet-marker-icon.leaflet-div-icon');
    const clusterCount = await clusters.count();
    console.log(`Found ${clusterCount} cluster markers`);
    
    // Check API response
    const apiResponse = await page.evaluate(async () => {
      const response = await fetch('http://54.203.54.74:8000/api/v1/sightings/with-coords');
      const data = await response.json();
      return {
        total: data.total,
        returned: data.sightings?.length || 0,
        firstFew: data.sightings?.slice(0, 3).map((s: any) => ({
          species: s.species,
          location: s.location
        }))
      };
    });
    
    console.log('API Response:', JSON.stringify(apiResponse, null, 2));
    
    // Check console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.waitForTimeout(2000);
    
    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }
    
    // Take screenshot for debugging
    await page.screenshot({ path: 'map-debug.png', fullPage: true });
    
    // Expect at least some markers or clusters
    expect(markerCount + clusterCount).toBeGreaterThan(0);
  });
  
  test('check API directly', async ({ request }) => {
    const response = await request.get('http://54.203.54.74:8000/api/v1/sightings/with-coords');
    const data = await response.json();
    
    console.log(`API returned ${data.total} total sightings`);
    console.log(`Actually returned ${data.sightings?.length || 0} sightings`);
    
    expect(response.ok()).toBeTruthy();
    expect(data.sightings).toBeDefined();
    expect(data.sightings.length).toBeGreaterThan(0);
  });
});