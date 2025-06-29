import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/store';
import { Filters } from '../../types';
import { ChevronLeft, ChevronRight, Filter, X, ChevronDown } from 'lucide-react';

export const FilterSidebar: React.FC = () => {
  const { filters, updateFilters, clearFilters, isSidebarOpen, setSidebarOpen, viewMode } = useStore();
  const [speciesDropdownOpen, setSpeciesDropdownOpen] = useState(false);
  const [sourceDropdownOpen, setSourceDropdownOpen] = useState(false);
  const [gmuInput, setGmuInput] = useState(
    filters.gmuList?.join(', ') || (filters.gmu ? filters.gmu.toString() : '') || ''
  );
  
  const speciesDropdownRef = useRef<HTMLDivElement>(null);
  const sourceDropdownRef = useRef<HTMLDivElement>(null);

  const speciesOptions = [
    'Bear', 'Elk', 'Deer', 'Moose', 'Pronghorn Antelope',
    'Bighorn Sheep', 'Mountain Lion', 'Mountain Goat', 'Hog', 'Marmot'
  ];

  const sourceOptions = [
    'Reddit', 'iNaturalist', '14ers.com', 'Google Places'
  ];
  
  // Sync GMU input with filters when they change externally
  useEffect(() => {
    setGmuInput(
      filters.gmuList?.join(', ') || (filters.gmu ? filters.gmu.toString() : '') || ''
    );
  }, [filters.gmu, filters.gmuList]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (speciesDropdownRef.current && !speciesDropdownRef.current.contains(event.target as Node)) {
        setSpeciesDropdownOpen(false);
      }
      if (sourceDropdownRef.current && !sourceDropdownRef.current.contains(event.target as Node)) {
        setSourceDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleFilterChange = (filterKey: keyof Filters, value: any) => {
    const newFilters = { ...filters, [filterKey]: value };
    // Apply filters immediately
    updateFilters(newFilters);
  };

  const handleClearFilters = () => {
    clearFilters();
  };
  
  const handleGmuSubmit = () => {
    const value = gmuInput.trim();
    
    // Allow empty input
    if (value === '') {
      const newFilters = { ...filters, gmu: undefined, gmuList: undefined };
      updateFilters(newFilters);
      return;
    }
    
    // Check if input contains comma
    if (value.includes(',')) {
      // Parse comma-separated values
      const gmuNumbers = value
        .split(',')
        .map(s => s.trim())
        .filter(s => s && /^\d+$/.test(s))
        .map(s => parseInt(s));
      
      const newFilters = { 
        ...filters, 
        gmuList: gmuNumbers.length > 0 ? gmuNumbers : undefined,
        gmu: undefined 
      };
      updateFilters(newFilters);
    } else {
      // Single value
      if (/^\d+$/.test(value)) {
        const num = parseInt(value);
        const newFilters = { 
          ...filters, 
          gmu: num,
          gmuList: undefined 
        };
        updateFilters(newFilters);
      }
    }
  };
  
  const handleSpeciesToggle = (species: string) => {
    const currentList = filters.speciesList || [];
    const lowerSpecies = species.toLowerCase();
    const newList = currentList.includes(lowerSpecies)
      ? currentList.filter(s => s !== lowerSpecies)
      : [...currentList, lowerSpecies];
    
    const newFilters = { 
      ...filters, 
      speciesList: newList.length > 0 ? newList : undefined,
      species: undefined 
    };
    updateFilters(newFilters);
  };
  
  const handleSourceToggle = (source: string) => {
    const currentList = filters.sourceList || [];
    const lowerSource = source.toLowerCase().replace(/\s+/g, '_');
    const newList = currentList.includes(lowerSource)
      ? currentList.filter(s => s !== lowerSource)
      : [...currentList, lowerSource];
    
    const newFilters = { 
      ...filters, 
      sourceList: newList.length > 0 ? newList : undefined,
      source: undefined 
    };
    updateFilters(newFilters);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  return (
    <>
      {/* Sidebar */}
      <div className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white dark:bg-gray-800 shadow-lg transition-transform duration-300 z-30 ${
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } w-80`}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="px-4 py-3 border-b dark:border-gray-700 flex items-center justify-between select-none">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Filters</h2>
            </div>
            <button
              onClick={handleClearFilters}
              className="text-sm text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Clear All
            </button>
          </div>

          {/* Filter Content */}
          <div className="flex-1 p-4 space-y-4 overflow-y-auto">
            {/* GMU Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 select-none">
                Game Management Units
              </label>
              <input
                type="text"
                placeholder="Enter GMU numbers (e.g., 12, 24, 36)"
                value={gmuInput}
                onChange={(e) => {
                  const value = e.target.value;
                  // Allow typing any input, including partial numbers
                  if (value === '' || /^[\d\s,]*$/.test(value)) {
                    setGmuInput(value);
                  }
                }}
                onBlur={handleGmuSubmit}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleGmuSubmit();
                    e.currentTarget.blur();
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 select-none">
                Separate multiple GMUs with commas
              </p>
            </div>

            {/* Species Filter */}
            <div ref={speciesDropdownRef} className="relative">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 select-none">
                Species
              </label>
              <button
                onClick={() => setSpeciesDropdownOpen(!speciesDropdownOpen)}
                className="w-full px-3 py-2 text-left border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center justify-between"
              >
                <span className="text-sm">
                  {filters.speciesList && filters.speciesList.length > 0
                    ? `${filters.speciesList.length} selected`
                    : 'All Species'}
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${speciesDropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              
              {speciesDropdownOpen && (
                <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg">
                  <div className="max-h-48 overflow-y-auto">
                    <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => {
                          const newFilters = { 
                            ...filters, 
                            speciesList: undefined,
                            species: undefined 
                          };
                          updateFilters(newFilters);
                        }}
                        className="w-full text-left text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1"
                      >
                        Clear All
                      </button>
                    </div>
                    <div className="p-2">
                      {speciesOptions.map(species => (
                        <div key={species} className="flex items-center space-x-2 hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded">
                          <input
                            type="checkbox"
                            id={`species-${species}`}
                            checked={(filters.speciesList || []).includes(species.toLowerCase())}
                            onChange={() => handleSpeciesToggle(species)}
                            className="rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer"
                          />
                          <label 
                            htmlFor={`species-${species}`}
                            className="text-sm text-gray-700 dark:text-gray-300 select-none cursor-pointer flex-1"
                          >
                            {species}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Source Filter */}
            <div ref={sourceDropdownRef} className="relative">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 select-none">
                Data Source
              </label>
              <button
                onClick={() => setSourceDropdownOpen(!sourceDropdownOpen)}
                className="w-full px-3 py-2 text-left border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center justify-between"
              >
                <span className="text-sm">
                  {filters.sourceList && filters.sourceList.length > 0
                    ? `${filters.sourceList.length} selected`
                    : 'All Sources'}
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${sourceDropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              
              {sourceDropdownOpen && (
                <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg">
                  <div>
                    <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => {
                          const newFilters = { 
                            ...filters, 
                            sourceList: undefined,
                            source: undefined 
                          };
                          updateFilters(newFilters);
                        }}
                        className="w-full text-left text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 p-1"
                      >
                        Clear All
                      </button>
                    </div>
                    <div className="p-2">
                      {sourceOptions.map(source => (
                        <div key={source} className="flex items-center space-x-2 hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded">
                          <input
                            type="checkbox"
                            id={`source-${source}`}
                            checked={(filters.sourceList || []).includes(source.toLowerCase().replace(/\s+/g, '_'))}
                            onChange={() => handleSourceToggle(source)}
                            className="rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer"
                          />
                          <label 
                            htmlFor={`source-${source}`}
                            className="text-sm text-gray-700 dark:text-gray-300 select-none cursor-pointer flex-1"
                          >
                            {source}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* GMU Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 select-none">
                GMU Options
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="exclude-no-gmu"
                  checked={filters.excludeNoGmu || false}
                  onChange={(e) => handleFilterChange('excludeNoGmu', e.target.checked)}
                  className="rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer"
                />
                <label 
                  htmlFor="exclude-no-gmu"
                  className="text-sm text-gray-700 dark:text-gray-300 select-none cursor-pointer"
                >
                  Only show entries with GMU assigned
                </label>
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 select-none">
                Date Range
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={filters.startDate ? new Date(filters.startDate).toISOString().split('T')[0] : ''}
                  onChange={(e) => handleFilterChange('startDate', e.target.value ? new Date(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Start date"
                />
                <input
                  type="date"
                  value={filters.endDate ? new Date(filters.endDate).toISOString().split('T')[0] : ''}
                  onChange={(e) => handleFilterChange('endDate', e.target.value ? new Date(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="End date"
                />
              </div>
            </div>

            {/* Location Accuracy Filter - Only show in map view */}
            {viewMode === 'map' && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Location Accuracy Filter
                  </label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="enable-accuracy-filter"
                      checked={filters.enableAccuracyFilter !== false}
                      onChange={(e) => updateFilters({ enableAccuracyFilter: e.target.checked })}
                      className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    />
                    <label htmlFor="enable-accuracy-filter" className="text-sm text-gray-600 dark:text-gray-400">
                      Enable
                    </label>
                  </div>
                </div>
                {filters.enableAccuracyFilter !== false && (
                  <>
                    <div className="flex items-center space-x-2">
                      <input
                        type="range"
                        min="1"
                        max="150"
                        step="1"
                        value={filters.maxLocationAccuracy || 10}
                        onChange={(e) => updateFilters({ maxLocationAccuracy: parseInt(e.target.value) })}
                        className="flex-1"
                      />
                      <span className="text-sm text-gray-600 dark:text-gray-400 w-16 text-right">
                        ≤ {filters.maxLocationAccuracy || 10} mi
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Only show locations with accuracy better than {filters.maxLocationAccuracy || 10} miles
                    </p>
                  </>
                )}
              </div>
            )}

          </div>

        </div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        className={`fixed top-1/2 -translate-y-1/2 ${isSidebarOpen ? 'left-80' : 'left-0'} z-30 bg-white dark:bg-gray-800 shadow-md rounded-r-md p-2 transition-all duration-300 hover:bg-gray-50 dark:hover:bg-gray-700`}
        aria-label="Toggle filters"
      >
        {isSidebarOpen ? (
          <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        )}
      </button>
    </>
  );
};
