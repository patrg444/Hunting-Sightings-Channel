import { test, expect } from '@playwright/test';

test('check API and console errors', async ({ page }) => {
  const consoleLogs: any[] = [];
  page.on('console', msg => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text()
    });
  });
  
  // Intercept API response
  const apiResponse = await page.waitForResponse(
    response => response.url().includes('/api/v1/sightings'),
    { timeout: 15000 }
  );
  
  await page.goto('http://54.203.54.74/');
  
  // Wait for response
  await page.waitForTimeout(5000);
  
  // Log console messages
  console.log('\nConsole logs:');
  consoleLogs.forEach(log => {
    if (log.type === 'error') {
      console.log(`ERROR: ${log.text}`);
    } else if (log.text.includes('sightings') || log.text.includes('accuracy')) {
      console.log(`${log.type}: ${log.text}`);
    }
  });
  
  // Check API response
  if (apiResponse) {
    const data = await apiResponse.json();
    console.log(`\nAPI returned ${data.total} total, ${data.items?.length || 0} items`);
  }
  
  // Check for map data in the page
  const mapInfo = await page.evaluate(() => {
    const mapContainer = document.querySelector('.leaflet-container');
    const markers = document.querySelectorAll('.leaflet-marker-icon');
    return {
      hasMap: !!mapContainer,
      markerCount: markers.length
    };
  });
  
  console.log(`\nMap exists: ${mapInfo.hasMap}, Markers: ${mapInfo.markerCount}`);
});