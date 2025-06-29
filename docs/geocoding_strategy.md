# Geocoding Strategy for Wildlife Sightings

## The Challenge
Wildlife sightings often have vague, relative, or descriptive locations that standard geocoding APIs can't handle:

### Examples of Problematic Descriptions:
- "about 2 miles up the trail from the parking lot"
- "near the creek crossing" 
- "somewhere in GMU 12"
- "between mile markers 3 and 4"
- "on the north face below treeline"
- "hunting the western drainages"

## Current Approach (LLM-based)
Using GPT-4 to estimate coordinates based on:
- Known landmark coordinates (Bear Lake, Mount Evans, etc.)
- Context clues (subreddit, other locations mentioned)
- General area knowledge

**Pros:**
- Can handle natural language
- Understands relative descriptions
- Can infer from context

**Cons:**
- Not always accurate
- Expensive at scale
- May hallucinate locations

## Better Solutions

### 1. Hierarchical Location Extraction
Extract multiple levels of location specificity:
```json
{
  "specific_location": "second switchback",
  "landmark": "Bear Lake Trail",
  "general_area": "Rocky Mountain National Park",
  "gmu": 20,
  "county": "Larimer",
  "state": "Colorado"
}
```
Then geocode the most specific identifiable location.

### 2. Trail/Feature Database
Build a database of:
- Trail coordinates with mile markers
- Known creek crossings
- Parking areas/trailheads
- Switchback locations
- Ridge lines and peaks

Then match descriptions to known features.

### 3. Hybrid Approach (Recommended)
```python
def smart_geocode(location_description):
    # 1. Try to extract known place names
    places = extract_place_names(location_description)  # "Bear Lake Trail"
    
    # 2. Geocode known places
    base_coords = geocode_known_places(places)
    
    # 3. Apply modifiers with LLM
    modifiers = extract_modifiers(location_description)  # "2 miles up", "near creek"
    
    # 4. Estimate final location
    if base_coords and modifiers:
        return apply_geographic_modifiers(base_coords, modifiers)
    elif base_coords:
        return base_coords
    else:
        # Fallback to LLM estimation
        return llm_estimate_location(location_description)
```

### 4. Crowdsourced Refinement
- Show estimated locations to users
- Allow corrections/refinements
- Build a mapping of descriptions → verified coordinates

### 5. GMU-Based Fallback
When all else fails, use the center of the GMU:
- "somewhere in unit 12" → center of GMU 12
- Set large confidence radius (20-40 miles)

## Implementation Priority

1. **Short term**: Continue with LLM + known landmarks
2. **Medium term**: Build trail/feature database from OpenStreetMap
3. **Long term**: Implement hybrid approach with user feedback

## Confidence Radius Guidelines

Based on location description quality:
- Specific landmark/trail + distance: 0.5-2 miles
- General trail/area name: 2-5 miles
- Park/wilderness area: 5-15 miles
- GMU only: 20-40 miles
- County/region: 40-80 miles
- "Colorado" or unknown: 100+ miles