import { test, expect } from '@playwright/test';

test('debug API calls', async ({ page }) => {
  // Listen to network requests
  const apiCalls: string[] = [];
  
  page.on('request', request => {
    if (request.url().includes('/api/v1/sightings')) {
      apiCalls.push(request.url());
    }
  });
  
  await page.goto('/');
  await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  
  // Click the exclude no GMU checkbox
  await page.click('input#exclude-no-gmu');
  await page.waitForTimeout(2000);
  
  // Check what API calls were made
  console.log('API calls made:');
  apiCalls.forEach(url => {
    console.log(url);
    // Check if exclude_no_gmu is in the URL
    if (url.includes('exclude_no_gmu')) {
      console.log('✓ Filter parameter found in URL');
    }
  });
  
  // Also check the table view
  await page.click('button:has-text("Table")');
  await page.waitForTimeout(2000);
  
  console.log('\nAPI calls after switching to table:');
  const recentCalls = apiCalls.slice(-3);
  recentCalls.forEach(url => console.log(url));
});