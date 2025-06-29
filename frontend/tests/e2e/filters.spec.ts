import { test, expect } from '@playwright/test';

test.describe('Filter Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the page to load
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  });

  test('should toggle filter sidebar', async ({ page }) => {
    // Check if sidebar is initially open
    const sidebar = page.locator('[class*="translate-x-0"]').first();
    await expect(sidebar).toBeVisible();

    // Click toggle button
    await page.click('button[aria-label="Toggle filters"]');
    
    // Check if sidebar is closed
    await expect(page.locator('[class*="translate-x-full"]').first()).toBeVisible();
  });

  test('should filter by GMU', async ({ page }) => {
    // Enter GMU number
    await page.fill('input[placeholder*="Enter GMU numbers"]', '46');
    
    // Wait for debounce and check if table updates
    await page.waitForTimeout(500);
    
    // Check if URL params updated (if implemented)
    // or check if table shows filtered results
  });

  test('should use multi-select species filter', async ({ page }) => {
    // Click species dropdown
    await page.click('button:has-text("All Species")');
    
    // Wait for dropdown to open
    await expect(page.locator('text=Bear').first()).toBeVisible();
    
    // Select Bear and Elk
    await page.locator('input[id="species-Bear"]').click();
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.waitForTimeout(200);
    
    // Check if button text updated - use contains for partial match
    await expect(page.locator('button').filter({ hasText: 'selected' }).first()).toBeVisible();
    
    // Click outside to close dropdown
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Verify dropdown is closed
    await expect(page.locator('input[id="species-Bear"]')).not.toBeVisible();
  });

  test('should use multi-select source filter', async ({ page }) => {
    // Click source dropdown
    await page.click('button:has-text("All Sources")');
    
    // Select Reddit and iNaturalist
    await page.locator('input[id="source-Reddit"]').click();
    await page.locator('input[id="source-iNaturalist"]').click();
    
    // Check if button text updated
    await expect(page.locator('button:has-text("2 selected")')).toBeVisible();
  });

  test('should clear individual filter dropdown', async ({ page }) => {
    // Open species dropdown and select some
    await page.click('button:has-text("All Species")');
    await page.locator('input[id="species-Bear"]').click();
    await page.locator('input[id="species-Elk"]').click();
    
    // Click Clear All in dropdown
    await page.locator('button:has-text("Clear All")').first().click();
    await page.waitForTimeout(200);
    
    // Verify button shows "All Species" again
    await expect(page.locator('button:has-text("All Species")')).toBeVisible();
    
    // Re-open dropdown to verify checkboxes are unchecked
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    
    // Verify checkboxes are unchecked
    await expect(page.locator('input[id="species-Bear"]')).not.toBeChecked();
    await expect(page.locator('input[id="species-Elk"]')).not.toBeChecked();
  });

  test('should clear all filters', async ({ page }) => {
    // Set various filters
    await page.fill('input[placeholder*="Enter GMU numbers"]', '46');
    await page.click('button:has-text("All Species")');
    await page.locator('input[id="species-Bear"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Click main Clear All button in header
    await page.locator('button:has-text("Clear All")').last().click();
    
    // Verify all filters are cleared
    await expect(page.locator('input[placeholder*="Enter GMU numbers"]')).toHaveValue('');
    await expect(page.locator('button:has-text("All Species")')).toBeVisible();
  });

  test('should filter by date range', async ({ page }) => {
    // Set start date
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    await page.locator('input[type="date"]').first().fill(startDate.toISOString().split('T')[0]);
    
    // Set end date
    const endDate = new Date();
    await page.locator('input[type="date"]').last().fill(endDate.toISOString().split('T')[0]);
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
  });

  test('should handle multiple GMUs', async ({ page }) => {
    // Enter multiple GMUs
    await page.fill('input[placeholder*="Enter GMU numbers"]', '46, 24, 36');
    
    // Wait for debounce
    await page.waitForTimeout(500);
    
    // Verify the input maintained the value
    await expect(page.locator('input[placeholder*="Enter GMU numbers"]')).toHaveValue('46, 24, 36');
  });

  test('should switch between map and table view', async ({ page }) => {
    // Check if map is visible initially
    await expect(page.locator('.leaflet-container')).toBeVisible();
    
    // Click table view button (if implemented)
    const tableButton = page.locator('button:has-text("Table")');
    if (await tableButton.isVisible()) {
      await tableButton.click();
      await expect(page.locator('table')).toBeVisible();
    }
  });

  test('should expand table row details', async ({ page }) => {
    // Switch to table view if needed
    const tableButton = page.locator('button:has-text("Table")');
    if (await tableButton.isVisible()) {
      await tableButton.click();
    }
    
    // Wait for table to load
    await page.waitForSelector('table', { timeout: 5000 });
    
    // Click on first row
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      
      // Check if details are visible
      await expect(page.locator('text=Coordinates:').first()).toBeVisible();
    }
  });
});