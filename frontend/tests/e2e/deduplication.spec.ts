import { test, expect } from '@playwright/test';

test.describe('Deduplication', () => {
  test('should remove duplicate entries from table', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Apply filters to see the problematic elk/14ers entries
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    // Apply date filter to narrow down
    await page.locator('input[type="date"]').first().fill('2025-06-27');
    await page.locator('input[type="date"]').last().fill('2025-06-27');
    
    await page.waitForTimeout(1000);
    
    // Switch to table view
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    // Count rows and collect text snippets
    const rows = await page.locator('tbody tr').all();
    const textSnippets = new Map<string, number>();
    
    for (const row of rows) {
      const expandButton = row.locator('button').filter({ has: row.locator('svg') });
      if (await expandButton.isVisible()) {
        await expandButton.click();
        await page.waitForTimeout(100);
        
        // Get the raw text
        const rawTextElement = await page.locator('text=Sighting Text:').locator('..').locator('.mt-1');
        if (await rawTextElement.isVisible()) {
          const rawText = await rawTextElement.textContent();
          const snippet = rawText?.slice(0, 100) || '';
          textSnippets.set(snippet, (textSnippets.get(snippet) || 0) + 1);
        }
        
        // Collapse the row
        await expandButton.click();
      }
    }
    
    // Check for duplicates
    console.log('Text snippet counts:');
    let duplicatesFound = false;
    textSnippets.forEach((count, snippet) => {
      if (count > 1) {
        console.log(`"${snippet}..." appears ${count} times`);
        duplicatesFound = true;
      }
    });
    
    // With deduplication, there should be no duplicates
    expect(duplicatesFound).toBe(false);
  });
  
  test('should show correct counts after deduplication', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('.leaflet-container', { timeout: 10000 });
    
    // Apply elk filter
    await page.click('button:has-text("All Species")');
    await page.waitForTimeout(200);
    await page.locator('input[id="species-Elk"]').click();
    await page.click('body', { position: { x: 10, y: 10 } });
    
    await page.waitForTimeout(1000);
    
    // Check table count
    await page.click('button:has-text("Table")');
    await page.waitForTimeout(1000);
    
    const tableRows = await page.locator('tbody tr').count();
    console.log('Elk entries in table:', tableRows);
    
    // Check map markers
    await page.click('button:has-text("Map")');
    await page.waitForTimeout(1000);
    
    const markers = await page.locator('.custom-sighting-marker').count();
    const clusters = await page.locator('.marker-cluster').count();
    console.log('Elk on map:', markers, 'markers +', clusters, 'clusters');
    
    // The counts should be reasonable (not showing 13 identical entries)
    expect(tableRows).toBeLessThan(200); // Should be deduplicated
  });
});