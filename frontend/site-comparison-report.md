# Site Comparison Report: Deployed vs Production

## Executive Summary

A comprehensive comparison between the deployed site (http://54.203.54.74/) and the production site (https://www.huntsightings.com/) reveals significant differences in functionality, UI design, and data display.

## Key Differences

### 1. **Map Markers**
- **Deployed Site**: Shows 16 wildlife sighting markers with different colors (green, orange, black)
- **Production Site**: Shows NO markers - the map is completely empty
- **Impact**: The production site is not displaying any wildlife sighting data

### 2. **Color Scheme**
- **Deployed Site**: 
  - Green-focused theme (rgb(21, 128, 61), rgb(22, 163, 74))
  - White background with black text
  - Green "Sign In" button
- **Production Site**: 
  - Blue-focused theme (rgb(3, 105, 161), rgb(37, 99, 235))
  - Transparent background
  - Blue "Apply Filters" button

### 3. **UI Components**

#### Header/Navigation
- **Deployed Site**: 
  - Green-themed header
  - "Markers" and "Heat Map" toggle buttons
  - "Sign In" button (green)
- **Production Site**: 
  - Blue-themed header  
  - "Please log in" text in header
  - No visible sign-in button in header

#### Sidebar
- **Deployed Site**:
  - Shows GMU filter with checkbox
  - "All Sources" dropdown for data sources
  - Date range inputs with actual date values
  - Location accuracy filter enabled
- **Production Site**:
  - Species dropdown set to "All Species"
  - "All Sources" dropdown for data sources
  - Date range inputs (empty)
  - Search radius feature
  - "Apply Filters" button at bottom

### 4. **Data Display**
- **Deployed Site**: Shows a data table below the map with sighting information
- **Production Site**: No data table visible

### 5. **Filter Options**
- **Deployed Site**:
  - GMU Options with checkbox
  - Location Accuracy Filter (enabled, ≤ 50 m)
- **Production Site**:
  - Species filter
  - Search Radius option
  - "No location selected" text

### 6. **Missing Features on Production**
- No wildlife sighting markers
- No data table
- No sign-in button in header
- No toggle for markers/heatmap view

## Technical Analysis

From the Playwright test results:
- **Deployed Site**: 
  - 16 Leaflet marker icons
  - 33 total marker elements
  - Data table present
- **Production Site**: 
  - 0 Leaflet marker icons
  - 1 marker element only
  - No data table

## Recommendations

1. **Critical Issue**: The production site is not loading or displaying any wildlife sighting data
2. **Authentication**: The production site appears to require login but lacks a visible sign-in button
3. **Feature Parity**: Several features present on the deployed site are missing from production
4. **UI Consistency**: Consider aligning the color schemes and UI components between environments

## Test Artifacts

Screenshots saved in: `frontend/screenshots-comparison/`
- Full page screenshots: `deployed-site.png`, `production-site.png`
- Map-only screenshots: `deployed-map-only.png`, `production-map-only.png`
