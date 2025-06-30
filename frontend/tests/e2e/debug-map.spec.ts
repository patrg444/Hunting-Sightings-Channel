import { test, expect } from '@playwright/test';

test.describe('Debug Map Issue', () => {
  test('debug map and API integration', async ({ page }) => {
    // Capture console messages
    const consoleLogs: any[] = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text()
      });
    });
    
    // Capture network requests
    const apiRequests: any[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method(),
          headers: request.headers()
        });
      }
    });
    
    // Capture network responses
    const apiResponses: any[] = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiResponses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    // Go to the page
    await page.goto('http://54.203.54.74/');
    
    // Wait for network idle
    await page.waitForLoadState('networkidle');
    
    // Wait a bit more for any async operations
    await page.waitForTimeout(5000);
    
    // Log all captured data
    console.log('\n=== CONSOLE LOGS ===');
    consoleLogs.forEach(log => {
      console.log(`[${log.type}] ${log.text}`);
    });
    
    console.log('\n=== API REQUESTS ===');
    apiRequests.forEach(req => {
      console.log(`${req.method} ${req.url}`);
    });
    
    console.log('\n=== API RESPONSES ===');
    apiResponses.forEach(res => {
      console.log(`${res.status} ${res.statusText} - ${res.url}`);
    });
    
    // Check if sightings are in the store
    const storeData = await page.evaluate(() => {
      // Try to access the store directly
      const storeElement = document.querySelector('[data-testid="sightings-count"]');
      return storeElement?.textContent || 'No sightings count found';
    });
    
    console.log('\n=== STORE DATA ===');
    console.log('Sightings count element:', storeData);
    
    // Check for map markers or clusters
    const mapData = await page.evaluate(() => {
      const markers = document.querySelectorAll('.leaflet-marker-icon');
      const clusters = document.querySelectorAll('.leaflet-marker-icon.leaflet-div-icon');
      const mapContainer = document.querySelector('.leaflet-container');
      
      return {
        markersCount: markers.length,
        clustersCount: clusters.length,
        mapExists: !!mapContainer,
        mapClasses: mapContainer?.className || 'no map container'
      };
    });
    
    console.log('\n=== MAP DATA ===');
    console.log('Map exists:', mapData.mapExists);
    console.log('Map classes:', mapData.mapClasses);
    console.log('Markers count:', mapData.markersCount);
    console.log('Clusters count:', mapData.clustersCount);
    
    // Take screenshot
    await page.screenshot({ path: 'debug-map.png', fullPage: true });
    
    // Check if the app is in an error state
    const errorMessage = await page.locator('.error-message, [role="alert"]').textContent().catch(() => null);
    if (errorMessage) {
      console.log('\n=== ERROR MESSAGE ===');
      console.log(errorMessage);
    }
  });
});