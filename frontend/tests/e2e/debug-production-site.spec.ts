import { test } from '@playwright/test';

test('debug production site issues', async ({ page }) => {
  // Monitor console and network
  const consoleLogs: any[] = [];
  const apiCalls: any[] = [];
  const apiResponses: any[] = [];
  
  page.on('console', msg => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text()
    });
  });
  
  page.on('request', request => {
    if (request.url().includes('/api/') || request.url().includes('supabase')) {
      apiCalls.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers()
      });
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/') || response.url().includes('supabase')) {
      apiResponses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
    }
  });
  
  // Go to production site
  await page.goto('https://www.huntsightings.com/', { waitUntil: 'networkidle' });
  
  // Wait for map to load
  await page.waitForSelector('.leaflet-container', { timeout: 10000 });
  await page.waitForTimeout(3000);
  
  console.log('\n=== CONSOLE LOGS ===');
  consoleLogs.forEach(log => {
    if (log.type === 'error' || log.text.includes('sighting') || log.text.includes('API')) {
      console.log(`[${log.type}] ${log.text}`);
    }
  });
  
  console.log('\n=== API CALLS ===');
  apiCalls.forEach(call => {
    console.log(`${call.method} ${call.url}`);
  });
  
  console.log('\n=== API RESPONSES ===');
  apiResponses.forEach(res => {
    console.log(`${res.status} ${res.statusText} - ${res.url}`);
  });
  
  // Check for authentication state
  const authInfo = await page.evaluate(() => {
    const loginText = document.body.textContent?.includes('Please log in');
    const signInButton = document.querySelector('button:has-text("Sign In")');
    const userData = window.localStorage.getItem('supabase.auth.token');
    
    return {
      hasLoginText: loginText,
      hasSignInButton: !!signInButton,
      hasAuthToken: !!userData,
      localStorage: Object.keys(window.localStorage)
    };
  });
  
  console.log('\n=== AUTHENTICATION STATE ===');
  console.log('Has "Please log in" text:', authInfo.hasLoginText);
  console.log('Has Sign In button:', authInfo.hasSignInButton);
  console.log('Has auth token:', authInfo.hasAuthToken);
  console.log('LocalStorage keys:', authInfo.localStorage);
  
  // Check the actual API endpoint being used
  const scriptContent = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script'));
    const apiScript = scripts.find(s => s.textContent?.includes('api') || s.textContent?.includes('backend'));
    return apiScript?.textContent?.substring(0, 500) || 'No API script found';
  });
  
  console.log('\n=== API CONFIGURATION ===');
  console.log(scriptContent);
  
  // Try to find out what backend it's using
  const networkInfo = await page.evaluate(() => {
    // Try to find any configuration in window object
    const config = (window as any).CONFIG || (window as any).__ENV__ || {};
    return {
      config,
      // Check if there's a different API URL in use
      apiUrl: (window as any).API_URL || (window as any).VITE_API_URL || 'not found'
    };
  });
  
  console.log('\n=== RUNTIME CONFIG ===');
  console.log('Config:', networkInfo.config);
  console.log('API URL:', networkInfo.apiUrl);
});