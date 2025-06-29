import { test, expect } from '@playwright/test';

test.describe('GMU Filter Results Count', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  });

  test('should show consistent results count between map and table views', async ({ page }) => {
    // First, get baseline counts without filter
    // Check table view
    await page.click('button:has-text("Table")');
    await page.waitForSelector('table', { timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const initialTableCount = await page.locator('tbody tr').count();
    console.log('Initial table row count:', initialTableCount);
    
    // Check map view markers
    await page.click('button:has-text("Map")');
    await page.waitForTimeout(1000);
    
    const initialMapMarkers = await page.locator('.leaflet-marker-icon').count();
    console.log('Initial map marker count:', initialMapMarkers);
    
    // Apply GMU filter
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    // Check map markers after filter
    const filteredMapMarkers = await page.locator('.leaflet-marker-icon').count();
    console.log('Filtered map marker count (GMU 46):', filteredMapMarkers);
    
    // Check table count after filter
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1500);
    
    const filteredTableCount = await page.locator('tbody tr').count();
    console.log('Filtered table row count (GMU 46):', filteredTableCount);
    
    // Both should be reduced
    expect(filteredMapMarkers).toBeLessThan(initialMapMarkers);
    expect(filteredTableCount).toBeLessThan(initialTableCount);
    
    // Log the reduction
    console.log(`Map markers reduced from ${initialMapMarkers} to ${filteredMapMarkers}`);
    console.log(`Table rows reduced from ${initialTableCount} to ${filteredTableCount}`);
  });

  test('should update counts when applying multiple GMU filters', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Apply single GMU filter
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    // Check table count with single GMU
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const singleGmuCount = await page.locator('tbody tr').count();
    console.log('Single GMU (46) count:', singleGmuCount);
    
    // Apply multiple GMU filter
    await page.click('button:has-text("Map")');
    await gmuInput.clear();
    await gmuInput.fill('46, 36, 24');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    // Check table count with multiple GMUs
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const multipleGmuCount = await page.locator('tbody tr').count();
    console.log('Multiple GMU (46, 36, 24) count:', multipleGmuCount);
    
    // Multiple GMUs should have more results than single GMU
    expect(multipleGmuCount).toBeGreaterThanOrEqual(singleGmuCount);
    
    // Verify all results match the filter
    const gmuCells = await page.locator('tbody tr td:nth-child(2)').allTextContents();
    for (const gmu of gmuCells) {
      expect(['46', '36', '24']).toContain(gmu.trim());
    }
  });

  test('should show zero results for non-existent GMU', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Apply filter for non-existent GMU
    await gmuInput.fill('999');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    // Check map markers
    const mapMarkers = await page.locator('.leaflet-marker-icon').count();
    console.log('Map markers for GMU 999:', mapMarkers);
    
    // Check table
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    const tableRows = await page.locator('tbody tr').count();
    console.log('Table rows for GMU 999:', tableRows);
    
    // Should show "No sightings found" message
    const noDataMessage = await page.locator('text=No sightings found').isVisible();
    expect(noDataMessage).toBe(true);
  });

  test('should properly clear GMU filter and restore all results', async ({ page }) => {
    // Get initial counts
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    const initialCount = await page.locator('tbody tr').count();
    
    // Apply GMU filter
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    const filteredCount = await page.locator('tbody tr').count();
    expect(filteredCount).toBeLessThan(initialCount);
    console.log(`Filtered from ${initialCount} to ${filteredCount} rows`);
    
    // Clear the filter
    await gmuInput.clear();
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    const clearedCount = await page.locator('tbody tr').count();
    console.log(`After clearing: ${clearedCount} rows`);
    
    // Should restore to initial count
    expect(clearedCount).toBe(initialCount);
  });

  test('should show real-time count in pagination info', async ({ page }) => {
    // Switch to table view
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    // Check pagination info
    const paginationInfo = page.locator('text=/Showing.*of.*results/');
    if (await paginationInfo.isVisible()) {
      const initialInfo = await paginationInfo.textContent();
      console.log('Initial pagination info:', initialInfo);
      
      // Apply GMU filter
      const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
      await gmuInput.fill('46');
      await gmuInput.press('Enter');
      await page.waitForTimeout(1500);
      
      // Check updated pagination info
      const filteredInfo = await paginationInfo.textContent();
      console.log('Filtered pagination info:', filteredInfo);
      
      // Extract total count from pagination text
      const initialMatch = initialInfo?.match(/of (\d+) results/);
      const filteredMatch = filteredInfo?.match(/of (\d+) results/);
      
      if (initialMatch && filteredMatch) {
        const initialTotal = parseInt(initialMatch[1]);
        const filteredTotal = parseInt(filteredMatch[1]);
        
        expect(filteredTotal).toBeLessThan(initialTotal);
        console.log(`Total results reduced from ${initialTotal} to ${filteredTotal}`);
      }
    }
  });

  test('should handle invalid GMU input gracefully', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Try to enter invalid characters
    await gmuInput.fill('abc');
    expect(await gmuInput.inputValue()).toBe('');
    
    // Try mixed valid/invalid
    await gmuInput.fill('46, abc, 24');
    expect(await gmuInput.inputValue()).toBe('46, , 24');
    
    // Submit and verify only valid GMUs are applied
    await gmuInput.clear();
    await gmuInput.fill('46, 24');
    await gmuInput.press('Enter');
    await page.waitForTimeout(1500);
    
    // Check table
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    const gmuCells = await page.locator('tbody tr td:nth-child(2)').allTextContents();
    for (const gmu of gmuCells) {
      expect(['46', '24']).toContain(gmu.trim());
    }
  });
});