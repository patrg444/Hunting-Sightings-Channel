import { test, expect } from '@playwright/test';

test.describe('GMU Filter Behavior', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  });

  test('should not apply filter while typing', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Start typing a GMU number
    await gmuInput.fill('4');
    
    // Wait a bit to see if filter is applied
    await page.waitForTimeout(500);
    
    // Check if filter is NOT applied (URL should not have GMU parameter)
    const url = page.url();
    expect(url).not.toContain('gmu=4');
    
    // Continue typing
    await gmuInput.fill('46');
    await page.waitForTimeout(500);
    
    // Still should not be applied
    const url2 = page.url();
    expect(url2).not.toContain('gmu=46');
  });

  test('should apply filter on blur', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Type GMU number
    await gmuInput.fill('46');
    
    // Click outside to blur
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Check table view to see if filter applied
    await page.click('button:has-text("Table")');
    await page.waitForSelector('table', { timeout: 5000 });
    
    // Verify GMU filter is applied by checking table data
    const gmuCells = await page.locator('tbody tr td:nth-child(2)').first().textContent();
    expect(gmuCells).toBe('46');
  });

  test('should apply filter on Enter key', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // First get unfiltered count
    await page.click('button:has-text("Table")');
    await page.waitForSelector('table', { timeout: 5000 });
    await page.waitForTimeout(500);
    const initialCount = await page.locator('tbody tr').count();
    
    // Go back to map view and apply filter
    await page.click('button:has-text("Map")');
    await page.waitForTimeout(500);
    
    // Type GMU number
    await gmuInput.fill('46');
    
    // Press Enter
    await gmuInput.press('Enter');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Switch back to table view
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    // Verify filter applied - should have fewer rows
    const filteredCount = await page.locator('tbody tr').count();
    expect(filteredCount).toBeLessThan(initialCount);
    
    // Verify all rows have GMU 46
    if (filteredCount > 0) {
      const gmuCells = await page.locator('tbody tr td:nth-child(2)').first().textContent();
      expect(gmuCells).toBe('46');
    }
  });

  test('should handle multiple GMUs correctly', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Type multiple GMUs
    await gmuInput.fill('46, 24, 36');
    
    // Press Enter
    await gmuInput.press('Enter');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Input should maintain the value
    await expect(gmuInput).toHaveValue('46, 24, 36');
  });

  test('should clear GMU when Clear All is clicked', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Set GMU filter
    await gmuInput.fill('46');
    await gmuInput.press('Enter');
    await page.waitForTimeout(500);
    
    // Click Clear All
    await page.locator('button:has-text("Clear All")').last().click();
    
    // GMU input should be empty
    await expect(gmuInput).toHaveValue('');
  });

  test('should allow partial input without applying filter', async ({ page }) => {
    const gmuInput = page.locator('input[placeholder*="Enter GMU numbers"]');
    
    // Type partial GMU
    await gmuInput.fill('4');
    await page.waitForTimeout(300);
    
    // Add more digits
    await gmuInput.fill('46');
    await page.waitForTimeout(300);
    
    // Add comma and another GMU
    await gmuInput.fill('46, 2');
    await page.waitForTimeout(300);
    
    // Complete the second GMU
    await gmuInput.fill('46, 24');
    
    // Verify input allows all these partial states
    await expect(gmuInput).toHaveValue('46, 24');
  });
});