import { test, expect } from '@playwright/test';

test('check deduplication impact on map', async ({ page }) => {
  // Enable console logging
  const consoleLogs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('duplicate') || text.includes('Loaded') || text.includes('Filtering')) {
      consoleLogs.push(text);
    }
  });
  
  await page.goto('http://54.203.54.74/');
  await page.waitForSelector('.leaflet-container');
  await page.waitForTimeout(5000);
  
  // Get sighting statistics from the page
  const stats = await page.evaluate(() => {
    // Count actual markers on the map
    const markers = document.querySelectorAll('.leaflet-marker-icon').length;
    const clusters = document.querySelectorAll('.marker-cluster').length;
    
    // Try to get the store data by triggering a re-render
    const mapContainer = document.querySelector('.leaflet-container');
    if (mapContainer) {
      mapContainer.dispatchEvent(new Event('click'));
    }
    
    return {
      markers,
      clusters,
      totalElements: markers + clusters
    };
  });
  
  console.log('\n=== MAP STATISTICS ===');
  console.log(`Individual markers: ${stats.markers}`);
  console.log(`Cluster markers: ${stats.clusters}`);
  console.log(`Total elements: ${stats.totalElements}`);
  
  console.log('\n=== RELEVANT LOGS ===');
  consoleLogs.forEach(log => console.log(log));
  
  // Check if deduplication is the issue
  if (consoleLogs.some(log => log.includes('duplicate'))) {
    console.log('\n⚠️  DEDUPLICATION IS ACTIVE AND REMOVING SIGHTINGS');
  }
});