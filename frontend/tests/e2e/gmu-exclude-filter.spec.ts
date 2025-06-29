import { test, expect } from '@playwright/test';

test.describe('GMU Exclude Filter', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  });

  test('should filter out entries without GMU', async ({ page }) => {
    // Switch to table view
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    // Count initial rows
    const initialRows = await page.locator('tbody tr').count();
    console.log('Initial rows:', initialRows);
    
    // Count rows with "-" in GMU column
    const noGmuRows = await page.locator('tbody tr td:nth-child(2)').filter({ hasText: '-' }).count();
    console.log('Rows without GMU:', noGmuRows);
    
    // Enable "Only show entries with GMU assigned" filter
    await page.click('input#exclude-no-gmu');
    await page.waitForTimeout(1500);
    
    // Count rows after filter
    const filteredRows = await page.locator('tbody tr').count();
    console.log('Rows after excluding no GMU:', filteredRows);
    
    // Should have fewer rows
    expect(filteredRows).toBeLessThan(initialRows);
    
    // Verify no "-" in GMU column
    const gmuCells = await page.locator('tbody tr td:nth-child(2)').allTextContents();
    for (const gmu of gmuCells) {
      expect(gmu).not.toBe('-');
      expect(gmu).toMatch(/^\d+$/); // Should be a number
    }
  });

  test('should work with other filters', async ({ page }) => {
    // Apply species filter first
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    await page.waitForTimeout(1000);
    
    // Switch to table and count
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    const elkRows = await page.locator('tbody tr').count();
    console.log('Elk entries:', elkRows);
    
    // Apply exclude no GMU filter
    await page.click('input#exclude-no-gmu');
    await page.waitForTimeout(1500);
    
    const elkWithGmuRows = await page.locator('tbody tr').count();
    console.log('Elk entries with GMU:', elkWithGmuRows);
    
    // Should have fewer rows
    expect(elkWithGmuRows).toBeLessThan(elkRows);
    
    // Verify all are elk and have GMU
    const speciesCells = await page.locator('tbody tr td:nth-child(3)').allTextContents();
    const gmuCells = await page.locator('tbody tr td:nth-child(2)').allTextContents();
    
    for (let i = 0; i < speciesCells.length; i++) {
      expect(speciesCells[i].toLowerCase()).toContain('elk');
      expect(gmuCells[i]).not.toBe('-');
    }
  });

  test('should update map markers when excluding no GMU', async ({ page }) => {
    // Count initial markers
    const initialMarkers = await page.locator('.custom-sighting-marker').count();
    const initialClusters = await page.locator('.marker-cluster').count();
    console.log('Initial map:', initialMarkers, 'markers +', initialClusters, 'clusters');
    
    // Apply exclude no GMU filter
    await page.click('input#exclude-no-gmu');
    await page.waitForTimeout(2000);
    
    // Count after filter
    const filteredMarkers = await page.locator('.custom-sighting-marker').count();
    const filteredClusters = await page.locator('.marker-cluster').count();
    console.log('Filtered map:', filteredMarkers, 'markers +', filteredClusters, 'clusters');
    
    // Total should be less
    const initialTotal = initialMarkers + initialClusters;
    const filteredTotal = filteredMarkers + filteredClusters;
    expect(filteredTotal).toBeLessThanOrEqual(initialTotal);
  });
});