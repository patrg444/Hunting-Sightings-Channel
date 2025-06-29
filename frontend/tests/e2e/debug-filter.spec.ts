import { test, expect } from '@playwright/test';

test.describe('Debug Filter Issue', () => {
  test('should toggle species checkboxes', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Open species dropdown
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(500);
    
    // Check initial state
    const bearCheckbox = page.locator('input[id="species-Bear"]');
    await expect(bearCheckbox).toBeVisible();
    
    // Get initial checked state
    const initialChecked = await bearCheckbox.isChecked();
    console.log('Initial checked state:', initialChecked);
    
    // Click checkbox
    await bearCheckbox.click();
    await page.waitForTimeout(500);
    
    // Check new state
    const afterClickChecked = await bearCheckbox.isChecked();
    console.log('After click checked state:', afterClickChecked);
    
    // Verify state changed
    expect(afterClickChecked).toBe(!initialChecked);
    
    // Check button text - find the dropdown button
    const dropdownButton = page.locator('button').filter({ has: page.locator('span:has-text("All Species")') }).or(page.locator('button').filter({ has: page.locator('span:has-text("selected")') }));
    const buttonText = await dropdownButton.first().textContent();
    console.log('Button text:', buttonText);
    
    // Expect it shows "1 selected"
    expect(buttonText).toContain('1 selected');
  });
});