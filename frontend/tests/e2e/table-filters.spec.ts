import { test, expect } from '@playwright/test';

test.describe('Table View Filter Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Switch to table view
    const tableButton = page.locator('button:has-text("Table")');
    if (await tableButton.isVisible()) {
      await tableButton.click();
      await page.waitForSelector('table', { timeout: 5000 });
    }
  });

  test('filters should apply to table data', async ({ page }) => {
    // Wait for initial data load
    await page.waitForTimeout(1000);
    
    // Count initial rows
    const initialRows = await page.locator('tbody tr').count();
    console.log('Initial row count:', initialRows);
    
    // Apply species filter
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.waitForTimeout(500);
    
    // Click outside to close dropdown
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Wait for table to update
    await page.waitForTimeout(1000);
    
    // Count filtered rows
    const filteredRows = await page.locator('tbody tr').count();
    console.log('Filtered row count:', filteredRows);
    
    // Verify filtering worked (should have fewer rows)
    expect(filteredRows).toBeLessThan(initialRows);
    
    // Verify all visible species are Elk
    const speciesCells = await page.locator('tbody tr td:nth-child(3)').allTextContents();
    for (const species of speciesCells) {
      expect(species.toLowerCase()).toContain('elk');
    }
  });

  test('multiple filters should work together', async ({ page }) => {
    // Apply GMU filter
    await page.fill('input[placeholder*="Enter GMU numbers"]', '46');
    await page.waitForTimeout(1000);
    
    // Apply species filter
    await page.click('button:has-text("All Species")');
    await page.locator('input[id="species-Bear"]').click();
    await page.locator('input[id="species-Elk"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Wait for filters to apply
    await page.waitForTimeout(1000);
    
    // Check if any rows exist
    const rowCount = await page.locator('tbody tr').count();
    console.log('Rows with GMU 46 and Bear/Elk:', rowCount);
    
    // If rows exist, verify they match filters
    if (rowCount > 0) {
      // Check GMU
      const gmuCells = await page.locator('tbody tr td:nth-child(2)').allTextContents();
      for (const gmu of gmuCells) {
        expect(gmu.trim()).toBe('46');
      }
      
      // Check species
      const speciesCells = await page.locator('tbody tr td:nth-child(3)').allTextContents();
      for (const species of speciesCells) {
        const lowerSpecies = species.toLowerCase();
        expect(lowerSpecies).toMatch(/bear|elk/);
      }
    }
  });

  test('pagination should work with filters', async ({ page }) => {
    // Apply a broad filter that returns many results
    await page.click('button:has-text("All Species")');
    await page.locator('input[id="species-Deer"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    await page.waitForTimeout(1000);
    
    // Check if pagination controls are visible
    const paginationNav = page.locator('nav[aria-label="Pagination"]');
    if (await paginationNav.isVisible()) {
      // Click next page
      const nextButton = page.locator('button').filter({ has: page.locator('svg') }).last();
      const isDisabled = await nextButton.getAttribute('disabled');
      
      if (isDisabled === null) {
        await nextButton.click();
        await page.waitForTimeout(1000);
        
        // Verify page changed
        const currentPageButton = page.locator('button.z-10');
        const pageText = await currentPageButton.textContent();
        expect(parseInt(pageText || '1')).toBeGreaterThan(1);
      }
    }
  });

  test('clear filters should reset table data', async ({ page }) => {
    // Apply filters
    await page.fill('input[placeholder*="Enter GMU numbers"]', '46');
    await page.click('button:has-text("All Species")');
    await page.locator('input[id="species-Bear"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    await page.waitForTimeout(1000);
    
    // Get filtered count
    const filteredCount = await page.locator('tbody tr').count();
    
    // Clear all filters
    await page.locator('button:has-text("Clear All")').last().click();
    await page.waitForTimeout(1000);
    
    // Get count after clearing
    const clearedCount = await page.locator('tbody tr').count();
    
    // Should have more rows after clearing filters
    expect(clearedCount).toBeGreaterThan(filteredCount);
  });
});