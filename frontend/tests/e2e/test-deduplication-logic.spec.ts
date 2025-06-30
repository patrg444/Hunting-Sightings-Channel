import { test } from '@playwright/test';

test('analyze deduplication impact', async ({ page }) => {
  // Intercept the store data
  await page.goto('http://54.203.54.74/');
  
  // Wait for data to load
  await page.waitForSelector('.leaflet-container');
  await page.waitForTimeout(5000);
  
  // Inject a script to analyze the deduplication
  const analysis = await page.evaluate(() => {
    // Create test data to understand deduplication
    const testSightings = [
      // Same species, same date, different locations
      { species: 'elk', sighting_date: '2024-01-01', location_name: 'Trail Ridge Road', raw_text: 'Saw elk' },
      { species: 'elk', sighting_date: '2024-01-01', location_name: 'Bear Lake', raw_text: 'Saw elk' },
      
      // Same species, same location, different dates
      { species: 'bear', sighting_date: '2024-01-01', location_name: 'RMNP', raw_text: 'Bear sighting' },
      { species: 'bear', sighting_date: '2024-01-02', location_name: 'RMNP', raw_text: 'Bear sighting' },
      
      // Same everything but different source
      { species: 'deer', sighting_date: '2024-01-01', location_name: 'GMU 1', source_type: 'reddit', raw_text: 'Deer' },
      { species: 'deer', sighting_date: '2024-01-01', location_name: 'GMU 1', source_type: 'iNaturalist', raw_text: 'Deer' },
    ];
    
    // Generate keys like the deduplication function does
    function generateKey(s: any) {
      const species = (s.species || '').toLowerCase().trim();
      const date = s.sighting_date || '';
      const source = (s.source_type || '').toLowerCase().trim();
      const text = (s.raw_text || '').slice(0, 100).trim();
      const location = (s.location_name || '').trim();
      return `${species}|${date}|${source}|${text}|${location}`;
    }
    
    const keys = testSightings.map((s, i) => ({
      index: i,
      sighting: s,
      key: generateKey(s)
    }));
    
    // Find duplicates
    const keyMap = new Map();
    keys.forEach(k => {
      if (!keyMap.has(k.key)) {
        keyMap.set(k.key, []);
      }
      keyMap.get(k.key).push(k.index);
    });
    
    const duplicates: any[] = [];
    keyMap.forEach((indices, key) => {
      if (indices.length > 1) {
        duplicates.push({ key, indices });
      }
    });
    
    return {
      testCount: testSightings.length,
      uniqueKeys: keyMap.size,
      duplicates,
      keys
    };
  });
  
  console.log('\n=== DEDUPLICATION ANALYSIS ===');
  console.log(`Test sightings: ${analysis.testCount}`);
  console.log(`Unique after dedup: ${analysis.uniqueKeys}`);
  console.log(`Would remove: ${analysis.testCount - analysis.uniqueKeys} sightings`);
  
  console.log('\n=== DUPLICATE GROUPS ===');
  analysis.duplicates.forEach(d => {
    console.log(`Key: ${d.key}`);
    console.log(`  Would keep 1, remove ${d.indices.length - 1}`);
  });
  
  console.log('\n=== DEDUPLICATION KEYS ===');
  analysis.keys.forEach(k => {
    console.log(`${k.index}: ${k.sighting.species} at ${k.sighting.location_name} => ${k.key}`);
  });
  
  // The issue is clear: deduplication is too aggressive
  console.log('\n⚠️  DEDUPLICATION IS TOO AGGRESSIVE!');
  console.log('It considers sightings duplicate even with different locations or dates');
});