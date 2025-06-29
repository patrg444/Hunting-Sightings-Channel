import { test, expect } from '@playwright/test';

test.describe('Manual GMU Filter Test', () => {
  test('check if exclude GMU filter is visible and working', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Open filter sidebar if not open
    const sidebar = page.locator('text=Game Management Units').first();
    if (!(await sidebar.isVisible())) {
      await page.click('button[aria-label="Toggle filters"]');
      await page.waitForTimeout(500);
    }
    
    // Check if the checkbox is visible
    const excludeGmuCheckbox = page.locator('input#exclude-no-gmu');
    const excludeGmuLabel = page.locator('label[for="exclude-no-gmu"]');
    
    console.log('Checkbox visible:', await excludeGmuCheckbox.isVisible());
    console.log('Label text:', await excludeGmuLabel.textContent());
    
    // Switch to table view to see initial data
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    // Count entries with no GMU (shown as "-")
    const noGmuCount = await page.locator('tbody tr td:nth-child(2):has-text("-")').count();
    console.log('Entries without GMU:', noGmuCount);
    
    // Check the exclude checkbox
    await excludeGmuCheckbox.click();
    console.log('Checkbox clicked, waiting for filter to apply...');
    await page.waitForTimeout(2000);
    
    // Count entries after filter
    const totalRows = await page.locator('tbody tr').count();
    console.log('Total rows after filter:', totalRows);
    
    // Count "-" entries again (should be 0)
    const noGmuAfterFilter = await page.locator('tbody tr td:nth-child(2):has-text("-")').count();
    console.log('Entries without GMU after filter:', noGmuAfterFilter);
    
    // All GMU values should be numbers
    const gmuValues = await page.locator('tbody tr td:nth-child(2)').allTextContents();
    console.log('Sample GMU values:', gmuValues.slice(0, 5));
    
    expect(noGmuAfterFilter).toBe(0);
  });
});