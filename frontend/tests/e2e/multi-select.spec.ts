import { test, expect } from '@playwright/test';

test.describe('Multi-Select Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  });

  test('multiple species selection works correctly', async ({ page }) => {
    // Open species dropdown
    const speciesButton = page.locator('button').filter({ hasText: /All Species|selected/ }).first();
    await speciesButton.click();
    
    // Wait for dropdown
    await page.waitForTimeout(200);
    
    // Click Bear
    const bearCheckbox = page.locator('input[id="species-Bear"]');
    await expect(bearCheckbox).toBeVisible();
    await bearCheckbox.click();
    await page.waitForTimeout(200);
    
    // Verify Bear is checked
    await expect(bearCheckbox).toBeChecked();
    
    // Click Elk
    const elkCheckbox = page.locator('input[id="species-Elk"]');
    await elkCheckbox.click();
    await page.waitForTimeout(200);
    
    // Verify both are checked
    await expect(bearCheckbox).toBeChecked();
    await expect(elkCheckbox).toBeChecked();
    
    // Check button text shows 2 selected
    const buttonText = await speciesButton.textContent();
    expect(buttonText).toContain('2 selected');
    
    // Test API call with both filters
    const response = await page.request.get('http://localhost:8002/api/v1/sightings?species_list=bear,elk&page_size=5');
    const data = await response.json();
    
    // Verify response has items
    expect(data.items).toBeDefined();
    console.log('API returned', data.items.length, 'items');
    
    // Verify each item is either bear or elk
    for (const item of data.items) {
      expect(['bear', 'elk']).toContain(item.species);
    }
  });

  test('unchecking individual items works', async ({ page }) => {
    // Open species dropdown
    const speciesButton = page.locator('button').filter({ hasText: /All Species|selected/ }).first();
    await speciesButton.click();
    
    // Select three species
    await page.locator('input[id="species-Bear"]').click();
    await page.waitForTimeout(100);
    await page.locator('input[id="species-Elk"]').click();
    await page.waitForTimeout(100);
    await page.locator('input[id="species-Deer"]').click();
    await page.waitForTimeout(100);
    
    // Verify 3 selected
    expect(await speciesButton.textContent()).toContain('3 selected');
    
    // Uncheck Elk
    await page.locator('input[id="species-Elk"]').click();
    await page.waitForTimeout(200);
    
    // Verify Elk is unchecked but others remain checked
    await expect(page.locator('input[id="species-Bear"]')).toBeChecked();
    await expect(page.locator('input[id="species-Elk"]')).not.toBeChecked();
    await expect(page.locator('input[id="species-Deer"]')).toBeChecked();
    
    // Verify button shows 2 selected
    expect(await speciesButton.textContent()).toContain('2 selected');
  });

  test('clear all in dropdown works', async ({ page }) => {
    // Open species dropdown
    const speciesButton = page.locator('button').filter({ hasText: /All Species|selected/ }).first();
    await speciesButton.click();
    
    // Select multiple
    await page.locator('input[id="species-Bear"]').click();
    await page.locator('input[id="species-Elk"]').click();
    await page.waitForTimeout(200);
    
    // Click Clear All in dropdown
    await page.locator('button:has-text("Clear All")').first().click();
    await page.waitForTimeout(200);
    
    // Verify button shows All Species (dropdown may close)
    expect(await speciesButton.textContent()).toContain('All Species');
    
    // Re-open dropdown to verify unchecked
    await speciesButton.click();
    await page.waitForTimeout(200);
    
    // Verify all unchecked
    await expect(page.locator('input[id="species-Bear"]')).not.toBeChecked();
    await expect(page.locator('input[id="species-Elk"]')).not.toBeChecked();
  });
});