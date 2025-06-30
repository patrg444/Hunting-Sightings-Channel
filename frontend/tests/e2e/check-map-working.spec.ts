import { test, expect } from '@playwright/test';

test('check if map is loading data', async ({ page }) => {
  const consoleLogs: any[] = [];
  const apiCalls: any[] = [];
  
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('sighting') || text.includes('API') || text.includes('accuracy') || msg.type() === 'error') {
      consoleLogs.push(`[${msg.type()}] ${text}`);
    }
  });
  
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      apiCalls.push({
        method: request.method(),
        url: request.url()
      });
    }
  });
  
  // Go to page
  await page.goto('http://54.203.54.74/');
  
  // Wait for map container
  await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  
  // Wait for any API calls
  await page.waitForTimeout(5000);
  
  // Log what we found
  console.log('\n=== CONSOLE LOGS ===');
  consoleLogs.forEach(log => console.log(log));
  
  console.log('\n=== API CALLS ===');
  apiCalls.forEach(call => console.log(`${call.method} ${call.url}`));
  
  // Check store state by looking at the page
  const storeInfo = await page.evaluate(() => {
    // Try to find any element that might show sighting count
    const countElements = Array.from(document.querySelectorAll('*')).filter(el => 
      el.textContent?.includes('sighting') || 
      el.textContent?.includes('result') ||
      el.textContent?.includes('found')
    );
    
    return countElements.map(el => el.textContent?.trim()).filter(Boolean).slice(0, 5);
  });
  
  console.log('\n=== POSSIBLE SIGHTING COUNTS ===');
  storeInfo.forEach(info => console.log(info));
  
  // Count map elements
  const mapData = await page.evaluate(() => {
    return {
      markers: document.querySelectorAll('.leaflet-marker-icon').length,
      clusters: document.querySelectorAll('.marker-cluster').length,
      panes: document.querySelectorAll('.leaflet-pane').length,
      tiles: document.querySelectorAll('.leaflet-tile').length
    };
  });
  
  console.log('\n=== MAP ELEMENTS ===');
  console.log(`Markers: ${mapData.markers}`);
  console.log(`Clusters: ${mapData.clusters}`);
  console.log(`Map panes: ${mapData.panes}`);
  console.log(`Map tiles loaded: ${mapData.tiles}`);
  
  // Take screenshot
  await page.screenshot({ path: 'map-state.png', fullPage: true });
});