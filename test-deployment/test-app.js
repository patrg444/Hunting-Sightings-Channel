const { chromium } = require('playwright');

async function testHuntingSightingsApp() {
  console.log('🧪 Starting Hunting Sightings Channel deployment test...\n');
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ Console error:', msg.text());
    }
  });
  
  try {
    // Test 1: Load the homepage
    console.log('📍 Test 1: Loading homepage...');
    await page.goto('http://54.203.54.74/', { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 
    });
    
    // Wait a bit for JavaScript to load
    await page.waitForTimeout(3000);
    
    const title = await page.title();
    console.log(`✅ Page loaded successfully. Title: "${title}"`);
    
    // Test 2: Check if map container exists
    console.log('\n📍 Test 2: Checking for map container...');
    const mapContainer = await page.locator('.leaflet-container').count();
    if (mapContainer > 0) {
      console.log('✅ Map container found');
    } else {
      console.log('❌ Map container not found');
    }
    
    // Test 3: Check for loading indicator
    console.log('\n📍 Test 3: Checking loading state...');
    const loadingIndicator = await page.locator('.animate-spin').count();
    if (loadingIndicator > 0) {
      console.log('⏳ Loading indicator present, waiting for data...');
      // Wait for loading to complete (max 10 seconds)
      await page.waitForSelector('.animate-spin', { state: 'hidden', timeout: 10000 }).catch(() => {});
    }
    
    // Test 4: Check API call
    console.log('\n📍 Test 4: Monitoring API calls...');
    const apiResponse = await page.waitForResponse(
      response => response.url().includes('/api/v1/sightings') && response.status() === 200,
      { timeout: 10000 }
    ).catch(() => null);
    
    if (apiResponse) {
      const responseData = await apiResponse.json();
      console.log(`✅ API call successful. Total sightings: ${responseData.total || responseData.items?.length || 0}`);
    } else {
      console.log('❌ No API response detected within 10 seconds');
    }
    
    // Test 5: Check for filter controls
    console.log('\n📍 Test 5: Checking filter controls...');
    const filters = {
      'Species filter': 'select[id*="species"], button:has-text("Species")',
      'GMU filter': 'select[id*="gmu"], button:has-text("GMU")',
      'Source filter': 'select[id*="source"], button:has-text("Source")',
      'Date filter': 'input[type="date"], button:has-text("Date")'
    };
    
    for (const [name, selector] of Object.entries(filters)) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        console.log(`✅ ${name} found`);
      } else {
        console.log(`❌ ${name} not found`);
      }
    }
    
    // Test 6: Check map markers or clusters
    console.log('\n📍 Test 6: Checking for map markers...');
    await page.waitForTimeout(2000); // Give map time to render
    const markers = await page.locator('.leaflet-marker-icon, .marker-cluster').count();
    if (markers > 0) {
      console.log(`✅ Found ${markers} map markers/clusters`);
    } else {
      console.log('❌ No map markers found');
    }
    
    // Test 7: Test view toggle
    console.log('\n📍 Test 7: Testing view toggle...');
    const viewToggle = await page.locator('button:has-text("Heat Map"), button:has-text("Table")').first();
    if (await viewToggle.count() > 0) {
      await viewToggle.click();
      await page.waitForTimeout(1000);
      console.log('✅ View toggle clicked successfully');
    } else {
      console.log('❌ View toggle not found');
    }
    
    // Test 8: Check for errors
    console.log('\n📍 Test 8: Checking for error messages...');
    const errorMessages = await page.locator('text=/error|failed|Error|Failed/i').count();
    if (errorMessages > 0) {
      console.log(`⚠️  Found ${errorMessages} potential error messages on page`);
    } else {
      console.log('✅ No error messages detected');
    }
    
    // Take screenshot
    console.log('\n📸 Taking screenshot...');
    await page.screenshot({ path: 'deployment-test.png', fullPage: true });
    console.log('✅ Screenshot saved as deployment-test.png');
    
  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
  } finally {
    await browser.close();
    console.log('\n✅ Test completed');
  }
}

// Run the test
testHuntingSightingsApp().catch(console.error);