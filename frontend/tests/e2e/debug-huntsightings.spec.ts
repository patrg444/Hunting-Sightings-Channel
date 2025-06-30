import { test } from '@playwright/test';

test('debug huntsightings.com deployment', async ({ page }) => {
  // Monitor all console and network activity
  const logs: any[] = [];
  
  page.on('console', msg => {
    logs.push({
      type: msg.type(),
      text: msg.text()
    });
  });
  
  page.on('requestfailed', request => {
    logs.push({
      type: 'failed',
      url: request.url(),
      failure: request.failure()
    });
  });
  
  console.log('\n🔍 Debugging huntsightings.com\n');
  
  // Go to production site
  await page.goto('https://www.huntsightings.com/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  
  // Check what API URL is being used
  const apiInfo = await page.evaluate(() => {
    // Check environment variables
    const viteApiUrl = (window as any).import?.meta?.env?.VITE_API_URL;
    
    // Check if there's a config object
    const config = (window as any).CONFIG || (window as any).__ENV__ || {};
    
    // Look for API calls in network
    const scripts = Array.from(document.querySelectorAll('script'));
    const hasApiProxy = scripts.some(s => s.textContent?.includes('/api/proxy'));
    
    return {
      viteApiUrl,
      config,
      hasApiProxy,
      windowKeys: Object.keys(window).filter(k => k.toLowerCase().includes('api'))
    };
  });
  
  console.log('API Configuration:');
  console.log('  VITE_API_URL:', apiInfo.viteApiUrl);
  console.log('  Has /api/proxy:', apiInfo.hasApiProxy);
  console.log('  Window API keys:', apiInfo.windowKeys);
  
  // Try to make an API call directly
  const apiTest = await page.evaluate(async () => {
    try {
      const response = await fetch('/api/proxy/api/v1/sightings/with-coords');
      return {
        success: true,
        status: response.status,
        url: response.url
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  });
  
  console.log('\nDirect API Test:');
  console.log('  Success:', apiTest.success);
  console.log('  Status:', apiTest.status);
  console.log('  URL:', apiTest.url);
  
  // Check for markers
  const mapData = await page.evaluate(() => {
    const markers = document.querySelectorAll('.leaflet-marker-icon').length;
    const hasMap = !!document.querySelector('.leaflet-container');
    const mapError = document.querySelector('.error-message')?.textContent;
    
    return {
      hasMap,
      markers,
      mapError
    };
  });
  
  console.log('\nMap Status:');
  console.log('  Has map:', mapData.hasMap);
  console.log('  Markers:', mapData.markers);
  console.log('  Errors:', mapData.mapError || 'None');
  
  // Show relevant console logs
  console.log('\nConsole Logs:');
  logs.filter(log => 
    log.type === 'error' || 
    log.text?.includes('api') || 
    log.text?.includes('sighting') ||
    log.type === 'failed'
  ).forEach(log => {
    console.log(`  [${log.type}] ${log.text || log.url}`);
    if (log.failure) console.log(`    Failure: ${log.failure.errorText}`);
  });
  
  // Take screenshot
  await page.screenshot({ path: 'huntsightings-debug.png', fullPage: true });
  console.log('\n📸 Screenshot saved: huntsightings-debug.png');
});