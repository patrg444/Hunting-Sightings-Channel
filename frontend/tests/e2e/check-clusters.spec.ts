import { test, expect } from '@playwright/test';

test('check cluster contents and zoom behavior', async ({ page }) => {
  await page.goto('http://54.203.54.74/');
  await page.waitForSelector('.leaflet-container');
  await page.waitForTimeout(3000);
  
  // Get initial state
  const initialState = await page.evaluate(() => {
    const markers = document.querySelectorAll('.leaflet-marker-icon:not(.leaflet-div-icon)').length;
    const clusters = Array.from(document.querySelectorAll('.marker-cluster')).map(c => ({
      count: c.textContent?.trim() || '0',
      class: c.className
    }));
    return { markers, clusters };
  });
  
  console.log('\n=== INITIAL STATE ===');
  console.log(`Individual markers: ${initialState.markers}`);
  console.log(`Clusters: ${initialState.clusters.length}`);
  initialState.clusters.forEach((c, i) => {
    console.log(`  Cluster ${i + 1}: ${c.count} sightings (${c.class})`);
  });
  
  // Calculate total sightings shown
  const totalInClusters = initialState.clusters.reduce((sum, c) => sum + parseInt(c.count), 0);
  const totalShown = initialState.markers + totalInClusters;
  console.log(`\nTotal sightings displayed: ${totalShown} (${initialState.markers} individual + ${totalInClusters} in clusters)`);
  
  // Click on the largest cluster to zoom in
  if (initialState.clusters.length > 0) {
    await page.click('.marker-cluster');
    await page.waitForTimeout(2000);
    
    const zoomedState = await page.evaluate(() => {
      const markers = document.querySelectorAll('.leaflet-marker-icon:not(.leaflet-div-icon)').length;
      const clusters = Array.from(document.querySelectorAll('.marker-cluster')).map(c => ({
        count: c.textContent?.trim() || '0'
      }));
      return { markers, clusters };
    });
    
    console.log('\n=== AFTER CLICKING CLUSTER ===');
    console.log(`Individual markers: ${zoomedState.markers}`);
    console.log(`Clusters: ${zoomedState.clusters.length}`);
    
    const totalInClustersZoomed = zoomedState.clusters.reduce((sum, c) => sum + parseInt(c.count), 0);
    const totalShownZoomed = zoomedState.markers + totalInClustersZoomed;
    console.log(`Total after zoom: ${totalShownZoomed}`);
  }
  
  // Check for deduplication by looking at the console
  const dedupeInfo = await page.evaluate(() => {
    // Try to access the deduplication stats if available
    const scripts = Array.from(document.querySelectorAll('script'));
    return scripts.some(s => s.textContent?.includes('deduplicate')) ? 'Deduplication is active' : 'No deduplication detected in scripts';
  });
  
  console.log(`\n${dedupeInfo}`);
  
  // Take screenshot of the map
  await page.screenshot({ path: 'map-clusters.png' });
});