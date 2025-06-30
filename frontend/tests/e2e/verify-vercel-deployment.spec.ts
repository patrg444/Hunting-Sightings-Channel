import { test, expect } from '@playwright/test';

test('verify Vercel deployment', async ({ page }) => {
  // Test the Vercel deployment URL
  console.log('\n🔍 Testing Vercel Deployment\n');
  
  await page.goto('https://frontend-37nq79u7m-hunting-sightings.vercel.app/');
  await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  await page.waitForTimeout(3000);
  
  // Check API calls
  const apiResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('/api/v1/sightings/with-coords');
      const data = await response.json();
      return {
        success: true,
        total: data.total,
        url: response.url
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
  
  console.log('API Response:', apiResponse);
  
  // Check map markers
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
      total: markers + totalInClusters
    };
  });
  
  console.log('\nMap Data:');
  console.log(`  Individual markers: ${mapData.individualMarkers}`);
  console.log(`  Clusters: ${mapData.clusterCount}`);
  console.log(`  Total sightings displayed: ${mapData.total}`);
  
  // Check if API proxy is working
  const proxyWorking = apiResponse.success && !apiResponse.url?.includes('54.203.54.74');
  console.log(`\nAPI Proxy: ${proxyWorking ? '✅ Working' : '❌ Not working'}`);
  
  if (mapData.total > 200) {
    console.log('\n✅ Vercel deployment is working correctly!');
  } else {
    console.log('\n⚠️ Vercel deployment may have issues');
  }
  
  expect(mapData.total).toBeGreaterThan(200);
});