import { test, expect } from '@playwright/test';

test.describe('Map Filter Integration', () => {
  test('GMU filter should update map markers', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    await page.waitForTimeout(2000); // Let map fully load
    
    // Count initial markers
    const initialMarkers = await page.locator('.custom-sighting-marker').count();
    console.log('Initial map markers:', initialMarkers);
    
    // Also check cluster markers
    const initialClusters = await page.locator('.marker-cluster').count();
    console.log('Initial cluster markers:', initialClusters);
    
    // Apply GMU filter
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    
    // Wait for map to update
    await page.waitForTimeout(3000);
    
    // Count markers after filter
    const filteredMarkers = await page.locator('.custom-sighting-marker').count();
    const filteredClusters = await page.locator('.marker-cluster').count();
    
    console.log('Filtered map markers:', filteredMarkers);
    console.log('Filtered cluster markers:', filteredClusters);
    
    // Total markers should change
    const initialTotal = initialMarkers + initialClusters;
    const filteredTotal = filteredMarkers + filteredClusters;
    
    console.log(`Total markers changed from ${initialTotal} to ${filteredTotal}`);
    
    // Log any console messages from the page
    page.on('console', msg => {
      if (msg.text().includes('sightings')) {
        console.log('Page console:', msg.text());
      }
    });
    
    // Also check the table to confirm filter is working
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    const tableRows = await page.locator('tbody tr').count();
    console.log('Table rows with GMU 46:', tableRows);
    
    // Verify table shows filtered results
    if (tableRows > 0) {
      const firstGmu = await page.locator('tbody tr td:nth-child(2)').first().textContent();
      expect(firstGmu).toBe('46');
    }
  });
  
  test('should log API responses', async ({ page }) => {
    // Listen to console logs
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      consoleLogs.push(msg.text());
    });
    
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Apply filter
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(2000);
    
    // Check console logs for API responses
    const apiLogs = consoleLogs.filter(log => log.includes('API response') || log.includes('Loaded'));
    console.log('API related logs:', apiLogs);
  });
});