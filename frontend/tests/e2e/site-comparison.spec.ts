import { test, expect } from '@playwright/test';
import fs from 'fs/promises';
import path from 'path';

test.describe('Site Comparison: Deployed vs Production', () => {
  test('capture and compare both sites', async ({ page }) => {
    const screenshotsDir = path.join(process.cwd(), 'screenshots-comparison');
    
    // Create screenshots directory
    await fs.mkdir(screenshotsDir, { recursive: true });

    // Configuration for both sites
    const sites = [
      {
        name: 'deployed',
        url: 'http://54.203.54.74/',
        screenshotPath: path.join(screenshotsDir, 'deployed-site.png')
      },
      {
        name: 'production',
        url: 'https://www.huntsightings.com/',
        screenshotPath: path.join(screenshotsDir, 'production-site.png')
      }
    ];

    // Set viewport for consistent screenshots
    await page.setViewportSize({ width: 1920, height: 1080 });

    for (const site of sites) {
      console.log(`\n📸 Capturing ${site.name} site: ${site.url}`);
      
      // Navigate to site
      await page.goto(site.url, { 
        waitUntil: 'networkidle',
        timeout: 60000 
      });

      // Wait for map to load (assuming there's a map element)
      try {
        await page.waitForSelector('canvas', { timeout: 10000 });
        console.log('✓ Map canvas detected');
      } catch (e) {
        console.log('ℹ No canvas element found (map might use different rendering)');
      }

      // Additional wait to ensure all elements are loaded
      await page.waitForTimeout(3000);

      // Take full page screenshot
      await page.screenshot({ 
        path: site.screenshotPath,
        fullPage: true
      });
      console.log(`✓ Screenshot saved: ${site.screenshotPath}`);

      // Analyze page elements
      console.log(`\n🔍 Analyzing ${site.name} site elements:`);

      // Count markers (common selectors for map markers)
      const markerSelectors = [
        '.marker',
        '.leaflet-marker-icon',
        '.mapboxgl-marker',
        '.map-marker',
        '[class*="marker"]',
        'img[src*="marker"]'
      ];

      let totalMarkers = 0;
      for (const selector of markerSelectors) {
        const count = await page.locator(selector).count();
        if (count > 0) {
          console.log(`  - Found ${count} elements matching "${selector}"`);
          totalMarkers += count;
        }
      }
      console.log(`  Total marker-like elements: ${totalMarkers}`);

      // Check for UI components
      const uiComponents = {
        'Navigation/Header': ['nav', 'header', '.navbar', '.navigation'],
        'Sidebar': ['.sidebar', 'aside', '[class*="sidebar"]'],
        'Map Container': ['.map', '#map', '[class*="map-container"]', '.mapboxgl-map', '.leaflet-container'],
        'Search/Filter': ['input[type="search"]', '.search', '.filter', '[class*="search"]'],
        'Buttons': ['button', '.btn', '[class*="button"]'],
        'Forms': ['form', '.form'],
        'Footer': ['footer', '.footer']
      };

      console.log('\n📋 UI Components:');
      for (const [component, selectors] of Object.entries(uiComponents)) {
        for (const selector of selectors) {
          const count = await page.locator(selector).count();
          if (count > 0) {
            console.log(`  ${component}: ${count} elements (${selector})`);
            break;
          }
        }
      }

      // Extract color scheme
      console.log('\n🎨 Color Scheme:');
      const colorInfo = await page.evaluate(() => {
        const body = document.body;
        const computedStyle = window.getComputedStyle(body);
        
        // Get primary colors from body
        const colors = {
          backgroundColor: computedStyle.backgroundColor,
          color: computedStyle.color,
          primaryColors: []
        };

        // Sample colors from various elements
        const elements = document.querySelectorAll('header, nav, .btn, button, a, h1, h2, h3');
        const colorSet = new Set();
        
        elements.forEach(el => {
          const style = window.getComputedStyle(el);
          if (style.backgroundColor && style.backgroundColor !== 'rgba(0, 0, 0, 0)') {
            colorSet.add(style.backgroundColor);
          }
          if (style.color) {
            colorSet.add(style.color);
          }
        });

        colors.primaryColors = Array.from(colorSet).slice(0, 10);
        return colors;
      });

      console.log(`  Background: ${colorInfo.backgroundColor}`);
      console.log(`  Text: ${colorInfo.color}`);
      if (colorInfo.primaryColors.length > 0) {
        console.log(`  Primary colors found: ${colorInfo.primaryColors.join(', ')}`);
      }

      // Check for specific features
      console.log('\n✨ Feature Detection:');
      const features = {
        'User Authentication': ['login', 'signin', 'logout', '[class*="auth"]', '[class*="user"]'],
        'Data Table/List': ['table', '.list', '[class*="table"]', '[class*="grid"]'],
        'Modal/Popup': ['.modal', '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]'],
        'Loading Indicators': ['.loading', '.spinner', '[class*="load"]'],
        'Error Messages': ['.error', '.alert', '[class*="error"]', '[class*="alert"]'],
        'Images': ['img', 'picture'],
        'Videos': ['video', 'iframe[src*="youtube"]', 'iframe[src*="vimeo"]']
      };

      for (const [feature, selectors] of Object.entries(features)) {
        let found = false;
        for (const selector of selectors) {
          const count = await page.locator(selector).count();
          if (count > 0) {
            console.log(`  ✓ ${feature}: Found (${count} elements)`);
            found = true;
            break;
          }
        }
        if (!found) {
          console.log(`  ✗ ${feature}: Not found`);
        }
      }

      // Get page title and any headings
      const title = await page.title();
      console.log(`\n📄 Page Title: "${title}"`);
      
      const h1Count = await page.locator('h1').count();
      if (h1Count > 0) {
        const h1Text = await page.locator('h1').first().textContent();
        console.log(`  Main Heading (H1): "${h1Text?.trim()}"`);
      }
    }

    console.log('\n\n🔄 Comparison Summary:');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`Screenshots saved in: ${screenshotsDir}`);
    console.log('- Deployed site: deployed-site.png');
    console.log('- Production site: production-site.png');
    console.log('\nTo visually compare the screenshots, you can:');
    console.log('1. Open both images side by side');
    console.log('2. Use an image diff tool');
    console.log('3. Run: npx playwright test --ui to see visual comparisons');
  });

  test('detailed map comparison', async ({ page }) => {
    const screenshotsDir = path.join(process.cwd(), 'screenshots-comparison');
    await fs.mkdir(screenshotsDir, { recursive: true });

    const sites = [
      {
        name: 'deployed',
        url: 'http://54.203.54.74/',
        mapScreenshot: path.join(screenshotsDir, 'deployed-map-only.png')
      },
      {
        name: 'production', 
        url: 'https://www.huntsightings.com/',
        mapScreenshot: path.join(screenshotsDir, 'production-map-only.png')
      }
    ];

    await page.setViewportSize({ width: 1920, height: 1080 });

    for (const site of sites) {
      console.log(`\n🗺️  Analyzing map on ${site.name} site`);
      
      await page.goto(site.url, { 
        waitUntil: 'networkidle',
        timeout: 60000 
      });

      // Wait for map to fully load
      await page.waitForTimeout(5000);

      // Try to find and screenshot just the map element
      const mapSelectors = ['.mapboxgl-map', '.leaflet-container', '#map', '.map-container', '[class*="map"]'];
      
      for (const selector of mapSelectors) {
        const mapElement = await page.locator(selector).first();
        const isVisible = await mapElement.isVisible().catch(() => false);
        
        if (isVisible) {
          console.log(`  Found map element: ${selector}`);
          
          // Get map bounds
          const box = await mapElement.boundingBox();
          if (box) {
            console.log(`  Map dimensions: ${box.width}x${box.height}`);
            
            // Screenshot just the map area
            await mapElement.screenshot({ path: site.mapScreenshot });
            console.log(`  ✓ Map screenshot saved: ${site.mapScreenshot}`);
          }
          
          // Try to get marker information from the map
          const mapInfo = await page.evaluate((sel) => {
            const mapEl = document.querySelector(sel);
            if (!mapEl) return null;
            
            // Count various marker types
            const markers = {
              leafletMarkers: mapEl.querySelectorAll('.leaflet-marker-icon').length,
              mapboxMarkers: mapEl.querySelectorAll('.mapboxgl-marker').length,
              customMarkers: mapEl.querySelectorAll('[class*="marker"]').length,
              images: mapEl.querySelectorAll('img').length,
              canvasElements: mapEl.querySelectorAll('canvas').length
            };
            
            return markers;
          }, selector);
          
          if (mapInfo) {
            console.log('  Marker counts:', mapInfo);
          }
          
          break;
        }
      }
    }
  });
});