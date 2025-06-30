const { chromium } = require('playwright');

async function testAPI() {
  console.log('🔍 Testing API and network requests...\n');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Log all network requests
  const requests = [];
  page.on('request', request => {
    if (request.url().includes('api')) {
      console.log(`📤 API Request: ${request.method()} ${request.url()}`);
      requests.push(request);
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('api')) {
      console.log(`📥 API Response: ${response.status()} ${response.url()}`);
    }
  });
  
  // Log console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      console.log(`❌ Console Error: ${text}`);
    } else if (text.includes('API') || text.includes('sighting')) {
      console.log(`📝 Console: ${text}`);
    }
  });
  
  try {
    console.log('Loading page...');
    await page.goto('http://54.203.54.74/', { waitUntil: 'domcontentloaded' });
    
    // Wait for potential API calls
    console.log('\nWaiting for API calls...');
    await page.waitForTimeout(5000);
    
    // Check if any API requests were made
    console.log(`\n📊 Total API requests made: ${requests.length}`);
    
    // Try to intercept the actual sightings data
    const sightingsData = await page.evaluate(() => {
      // Check if there's any sightings data in window or store
      if (window.__INITIAL_DATA__) return window.__INITIAL_DATA__;
      
      // Try to find React/Vue/Svelte store
      const rootEl = document.querySelector('#root') || document.querySelector('#app');
      if (rootEl && rootEl._reactRootContainer) {
        // React app - try to access store
        return 'React app detected';
      }
      
      // Check localStorage
      const stored = localStorage.getItem('sightings');
      if (stored) return JSON.parse(stored);
      
      return null;
    });
    
    console.log('\n🔍 Sightings data found:', sightingsData ? 'Yes' : 'No');
    
    // Check network panel for blocked requests
    const failedRequests = await page.evaluate(() => {
      return performance.getEntriesByType('resource')
        .filter(entry => entry.name.includes('api'))
        .map(entry => ({
          url: entry.name,
          duration: entry.duration,
          status: entry.transferSize === 0 ? 'blocked/failed' : 'success'
        }));
    });
    
    console.log('\n📊 Network performance entries:');
    failedRequests.forEach(req => {
      console.log(`  ${req.status === 'success' ? '✅' : '❌'} ${req.url} (${req.duration.toFixed(2)}ms)`);
    });
    
    // Make a direct API call to test
    console.log('\n🧪 Making direct API call...');
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('http://54.203.54.74:8000/api/v1/sightings?page_size=5');
        const data = await response.json();
        return { status: response.status, data };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    if (apiResponse.error) {
      console.log(`❌ Direct API call failed: ${apiResponse.error}`);
    } else {
      console.log(`✅ Direct API call successful: Status ${apiResponse.status}`);
      console.log(`   Total sightings: ${apiResponse.data.total}`);
      console.log(`   Items returned: ${apiResponse.data.items?.length || 0}`);
    }
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await browser.close();
  }
}

testAPI().catch(console.error);