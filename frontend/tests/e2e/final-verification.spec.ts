import { test, expect } from '@playwright/test';

test.describe('Final Deployment Verification', () => {
  test('verify all fixes are working', async ({ page }) => {
    console.log('\n🚀 FINAL DEPLOYMENT VERIFICATION\n');
    
    // Go to deployed site
    await page.goto('http://54.203.54.74/');
    await page.waitForSelector('.leaflet-container');
    await page.waitForTimeout(5000);
    
    // 1. Check API connection
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('http://54.203.54.74:8000/api/v1/sightings/with-coords');
        const data = await response.json();
        return {
          success: true,
          total: data.total,
          returned: data.sightings?.length || 0
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    console.log('✅ API Connection:', apiResponse.success ? 'Working' : 'Failed');
    if (apiResponse.success) {
      console.log(`   Total sightings in DB: ${apiResponse.total}`);
      console.log(`   Sightings returned: ${apiResponse.returned}`);
    }
    
    // 2. Check map markers
    const mapData = await page.evaluate(() => {
      const markers = document.querySelectorAll('.leaflet-marker-icon:not(.leaflet-div-icon)').length;
      const clusters = Array.from(document.querySelectorAll('.marker-cluster')).map(c => 
        parseInt(c.textContent?.trim() || '0')
      );
      const totalInClusters = clusters.reduce((sum, count) => sum + count, 0);
      
      return {
        individualMarkers: markers,
        clusterCount: clusters.length,
        totalInClusters,
        total: markers + totalInClusters,
        clusters
      };
    });
    
    console.log('\n✅ Map Display:');
    console.log(`   Individual markers: ${mapData.individualMarkers}`);
    console.log(`   Clusters: ${mapData.clusterCount}`);
    console.log(`   Total sightings displayed: ${mapData.total}`);
    
    // 3. Check accuracy filter
    await page.click('button[aria-label="Toggle filters"]');
    await page.waitForSelector('text="Location Accuracy Filter"');
    
    const filterValue = await page.textContent('text=/Only show locations with accuracy better than \\d+ miles/');
    console.log('\n✅ Accuracy Filter:');
    console.log(`   Current setting: ${filterValue}`);
    
    // 4. Check deduplication
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.text().includes('duplicate') || msg.text().includes('Loaded')) {
        consoleMessages.push(msg.text());
      }
    });
    
    // Reload page to capture console messages
    await page.reload();
    await page.waitForTimeout(3000);
    
    const loadedMessage = consoleMessages.find(msg => msg.includes('Loaded'));
    if (loadedMessage) {
      console.log('\n✅ Data Loading:');
      console.log(`   ${loadedMessage}`);
    }
    
    // 5. Performance check
    const performanceData = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domReady: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart
      };
    });
    
    console.log('\n✅ Performance:');
    console.log(`   Page load time: ${performanceData.loadTime}ms`);
    console.log(`   DOM ready time: ${performanceData.domReady}ms`);
    
    // 6. Check data table
    const tableData = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr').length;
      return { hasTable: rows > 0, rowCount: rows };
    });
    
    console.log('\n✅ Data Table:');
    console.log(`   Table present: ${tableData.hasTable ? 'Yes' : 'No'}`);
    if (tableData.hasTable) {
      console.log(`   Rows displayed: ${tableData.rowCount}`);
    }
    
    // Summary
    console.log('\n📊 DEPLOYMENT SUMMARY');
    console.log('════════════════════════════════════════');
    console.log(`Total sightings in system: ${apiResponse.total || 'Unknown'}`);
    console.log(`Sightings displayed on map: ${mapData.total}`);
    console.log(`Accuracy filter: ${filterValue?.includes('100') ? '✅ Set to 100 miles' : '⚠️ Not set to 100 miles'}`);
    console.log(`API Status: ${apiResponse.success ? '✅ Working' : '❌ Failed'}`);
    console.log(`Map Status: ${mapData.total > 200 ? '✅ Showing 200+ markers' : '⚠️ Less than expected'}`);
    
    // Assertions
    expect(apiResponse.success).toBeTruthy();
    expect(mapData.total).toBeGreaterThan(200);
    expect(filterValue).toContain('100 miles');
    
    // Take final screenshot
    await page.screenshot({ path: 'final-deployment-screenshot.png', fullPage: true });
    console.log('\n📸 Screenshot saved: final-deployment-screenshot.png');
  });
  
  test('compare with production issues', async ({ page }) => {
    console.log('\n🔍 PRODUCTION SITE COMPARISON\n');
    
    // Check production site
    await page.goto('https://www.huntsightings.com/');
    await page.waitForSelector('.leaflet-container');
    
    const prodData = await page.evaluate(() => {
      const markers = document.querySelectorAll('.leaflet-marker-icon').length;
      const config = (window as any).CONFIG || {};
      return {
        markers,
        apiUrl: config.API_URL || 'not found'
      };
    });
    
    console.log('❌ Production Site Issues:');
    console.log(`   Markers displayed: ${prodData.markers} (should be 200+)`);
    console.log(`   API URL: ${prodData.apiUrl} (should NOT be localhost)`);
    console.log('\n⚠️  Production site needs urgent fix!');
  });
});