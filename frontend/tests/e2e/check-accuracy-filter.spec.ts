import { test, expect } from '@playwright/test';

test.describe('Accuracy Filter Update', () => {
  test('should show more markers with 50-mile filter', async ({ page }) => {
    // Go to production site
    await page.goto('http://54.203.54.74/', { waitUntil: 'domcontentloaded' });
    
    // Wait for map to load
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Wait for potential markers to load
    await page.waitForTimeout(5000);
    
    // Count markers
    const markers = await page.locator('.leaflet-marker-icon').count();
    console.log(`Found ${markers} markers with updated filter`);
    
    // Should have significantly more markers than the 14 we had with 10-mile filter
    expect(markers).toBeGreaterThan(50);
  });
  
  test('check filter UI shows 50 miles default', async ({ page }) => {
    await page.goto('http://54.203.54.74/', { waitUntil: 'domcontentloaded' });
    
    // Click filter button to open sidebar
    await page.click('button[aria-label="Toggle filters"]');
    
    // Wait for sidebar
    await page.waitForSelector('text="Location Accuracy Filter"', { timeout: 5000 });
    
    // Check if the text shows 50 miles
    const accuracyText = await page.textContent('text=/Only show locations with accuracy better than \\d+ miles/');
    console.log('Accuracy filter text:', accuracyText);
    
    expect(accuracyText).toContain('50 miles');
  });
});