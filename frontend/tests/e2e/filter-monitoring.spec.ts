import { test, expect } from '@playwright/test';

test.describe('Filter Results Monitoring', () => {
  test('comprehensive GMU filter monitoring', async ({ page }) => {
    // Capture console logs
    const logs: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('sightings') || msg.text().includes('API')) {
        logs.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    console.log('\n=== INITIAL STATE ===');
    
    // Check initial map state
    const initialMarkers = await page.locator('.custom-sighting-marker').count();
    const initialClusters = await page.locator('.marker-cluster').count();
    console.log(`Map: ${initialMarkers} markers + ${initialClusters} clusters = ${initialMarkers + initialClusters} total`);
    
    // Check initial table state
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const initialTableRows = await page.locator('tbody tr').count();
    console.log(`Table: ${initialTableRows} rows`);
    
    // Check pagination info
    const paginationInfo = await page.locator('text=/Showing.*of.*results/').textContent();
    console.log(`Pagination: ${paginationInfo}`);
    
    console.log('\n=== APPLYING GMU 46 FILTER ===');
    
    // Go back to map and apply filter
    await page.click('button:has-text("Map")');
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(2000);
    
    // Check filtered map state
    const filteredMarkers = await page.locator('.custom-sighting-marker').count();
    const filteredClusters = await page.locator('.marker-cluster').count();
    console.log(`Map: ${filteredMarkers} markers + ${filteredClusters} clusters = ${filteredMarkers + filteredClusters} total`);
    
    // Check filtered table state
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const filteredTableRows = await page.locator('tbody tr').count();
    console.log(`Table: ${filteredTableRows} rows`);
    
    // Check updated pagination
    const filteredPaginationInfo = await page.locator('text=/Showing.*of.*results/').textContent();
    console.log(`Pagination: ${filteredPaginationInfo}`);
    
    // Verify all table rows are GMU 46
    if (filteredTableRows > 0) {
      const gmuValues = await page.locator('tbody tr td:nth-child(2)').allTextContents();
      const uniqueGmus = [...new Set(gmuValues)];
      console.log(`Unique GMUs in table: ${uniqueGmus.join(', ')}`);
      expect(uniqueGmus).toEqual(['46']);
    }
    
    console.log('\n=== APPLYING MULTIPLE GMU FILTER ===');
    
    // Apply multiple GMUs
    await page.click('button:has-text("Map")');
    await gmuInput.clear();
    await gmuInput.fill('46, 36, 24');
    await gmuInput.press('Enter');
    await page.waitForTimeout(2000);
    
    // Check multi-GMU results
    const multiMarkers = await page.locator('.custom-sighting-marker').count();
    const multiClusters = await page.locator('.marker-cluster').count();
    console.log(`Map: ${multiMarkers} markers + ${multiClusters} clusters = ${multiMarkers + multiClusters} total`);
    
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const multiTableRows = await page.locator('tbody tr').count();
    console.log(`Table: ${multiTableRows} rows`);
    
    const multiPaginationInfo = await page.locator('text=/Showing.*of.*results/').textContent();
    console.log(`Pagination: ${multiPaginationInfo}`);
    
    // Verify GMUs
    if (multiTableRows > 0) {
      const gmuValues = await page.locator('tbody tr td:nth-child(2)').allTextContents();
      const uniqueGmus = [...new Set(gmuValues)].sort();
      console.log(`Unique GMUs in table: ${uniqueGmus.join(', ')}`);
      
      // Each row should be one of the filtered GMUs
      for (const gmu of gmuValues) {
        expect(['46', '36', '24', '-']).toContain(gmu.trim());
      }
    }
    
    console.log('\n=== API LOGS ===');
    logs.forEach(log => console.log(log));
  });
  
  test('species filter monitoring', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    console.log('\n=== SPECIES FILTER TEST ===');
    
    // Apply species filter
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    await page.waitForTimeout(2000);
    
    // Check map
    const elkMarkers = await page.locator('.custom-sighting-marker').count();
    const elkClusters = await page.locator('.marker-cluster').count();
    console.log(`Elk on map: ${elkMarkers} markers + ${elkClusters} clusters`);
    
    // Check table
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const elkRows = await page.locator('tbody tr').count();
    console.log(`Elk in table: ${elkRows} rows`);
    
    // Verify species
    if (elkRows > 0) {
      const speciesValues = await page.locator('tbody tr td:nth-child(3)').allTextContents();
      const uniqueSpecies = [...new Set(speciesValues)];
      console.log(`Species found: ${uniqueSpecies.join(', ')}`);
      
      // All should be Elk
      for (const species of speciesValues) {
        expect(species.toLowerCase()).toContain('elk');
      }
    }
  });
});