# Location Confidence Radius Feature Implementation

## Overview
The location confidence radius feature has been added to the LLM validator to estimate the accuracy/precision of location information in wildlife sighting reports. Rather than extracting mentioned radii, this feature asks the LLM to estimate how precise the location is, providing a confidence radius in miles.

## Implementation Details

### Modified Methods

1. **`validate_sighting_with_llm()`**
   - Added `location_confidence_radius` field to the JSON schema in the prompt
   - Added guidelines for estimating location precision (0.5-50+ miles)
   - Added examples showing different confidence radii based on location specificity

2. **`analyze_full_text_for_sighting()`**
   - Added `location_confidence_radius` field to the JSON schema in the prompt
   - Added 'location_confidence_radius' to the location_fields list
   - Added guidelines and examples for confidence estimation

### Location Confidence Radius Specification
- **Type**: Float (miles)
- **Purpose**: Estimates how accurate/precise the location information is
- **Range Guidelines**:
  - **0.5-2 miles**: Very precise (GPS coordinates, specific trail markers)
  - **2-5 miles**: Fairly specific (named peaks, lakes, campgrounds)
  - **5-15 miles**: Moderate precision (small towns, specific drainages)
  - **20-50 miles**: General area (GMU only, county level)
  - **50+ miles**: Very vague or no specific location

## Usage Examples

### Example 1: Precise Location
```python
context = "Spotted elk at the bridge on Maroon Creek Trail at mile marker 3.5"
is_valid, confidence, location_data = validator.validate_sighting_with_llm(context, "elk", "elk")
# location_data will include: {'location_confidence_radius': 1, 'location_name': 'Maroon Creek Trail', ...}
```

### Example 2: Vague Location
```python
context = "Saw some deer somewhere in GMU 23"
is_valid, confidence, location_data = validator.validate_sighting_with_llm(context, "deer", "deer")
# location_data will include: {'location_confidence_radius': 40, 'gmu_number': 23, ...}
```

### Example 3: Full Text Analysis
```python
full_text = "Bear spotted near Independence Pass campground yesterday morning"
result = validator.analyze_full_text_for_sighting(full_text, ["bear"])
# result will include: {'location_confidence_radius': 3, 'location_name': 'Independence Pass campground', ...}
```

## Testing
A test script has been created at `scripts/test_radius_feature.py` to verify the radius extraction functionality with various test cases.

## Benefits
1. **Location Accuracy Assessment**: Understand how precise each sighting location is
2. **Better Filtering**: Users can filter sightings by location precision
3. **Mapping Enhancement**: Can display confidence circles on maps showing location uncertainty
4. **Data Quality**: Helps identify which sightings have reliable vs. vague location data

## Future Enhancements
- Machine learning to improve confidence radius estimation
- Integration with mapping to show uncertainty visualization
- Combine with elevation data for better precision estimates
- Use confidence radius for sighting clustering algorithms