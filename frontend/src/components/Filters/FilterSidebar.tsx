import React, { useState } from 'react';
import { useStore } from '../../store/store';
import { Filters } from '../../types';
import { ChevronLeft, ChevronRight, Filter, X } from 'lucide-react';

export const FilterSidebar: React.FC = () => {
  const { filters, updateFilters, clearFilters, isSidebarOpen, setSidebarOpen } = useStore();
  const [localFilters, setLocalFilters] = useState<Filters>(filters);

  const speciesOptions = [
    'Elk', 'Deer', 'Bear', 'Moose', 'Mountain Lion', 
    'Turkey', 'Duck', 'Goose', 'Other'
  ];

  const sourceOptions = [
    'Reddit', 'iNaturalist', 'eBird', 'Observation.org', 
    '14ers.com', 'SummitPost', 'Google Places'
  ];

  const handleFilterChange = (filterKey: keyof Filters, value: any) => {
    const newFilters = { ...localFilters, [filterKey]: value };
    setLocalFilters(newFilters);
  };

  const applyFilters = () => {
    updateFilters(localFilters);
  };

  const handleClearFilters = () => {
    setLocalFilters({});
    clearFilters();
  };

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  return (
    <>
      {/* Sidebar */}
      <div className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white shadow-lg transition-transform duration-300 z-30 ${
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } w-80`}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold">Filters</h2>
            </div>
            <button
              onClick={handleClearFilters}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Clear All
            </button>
          </div>

          {/* Filter Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* GMU Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Game Management Unit
              </label>
              <input
                type="number"
                placeholder="Enter GMU number"
                value={localFilters.gmu || ''}
                onChange={(e) => handleFilterChange('gmu', e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Species Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Species
              </label>
              <select
                value={localFilters.species || ''}
                onChange={(e) => handleFilterChange('species', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Species</option>
                {speciesOptions.map(species => (
                  <option key={species} value={species.toLowerCase()}>
                    {species}
                  </option>
                ))}
              </select>
            </div>

            {/* Source Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Source
              </label>
              <select
                value={localFilters.source || ''}
                onChange={(e) => handleFilterChange('source', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Sources</option>
                {sourceOptions.map(source => (
                  <option key={source} value={source.toLowerCase().replace(/\s+/g, '_')}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date Range
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={localFilters.startDate ? new Date(localFilters.startDate).toISOString().split('T')[0] : ''}
                  onChange={(e) => handleFilterChange('startDate', e.target.value ? new Date(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Start date"
                />
                <input
                  type="date"
                  value={localFilters.endDate ? new Date(localFilters.endDate).toISOString().split('T')[0] : ''}
                  onChange={(e) => handleFilterChange('endDate', e.target.value ? new Date(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="End date"
                />
              </div>
            </div>

            {/* Location-based Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Radius
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Click on the map to set a center point
              </p>
              {(localFilters.lat && localFilters.lon) ? (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">
                    Center: {localFilters.lat.toFixed(4)}, {localFilters.lon.toFixed(4)}
                  </p>
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={localFilters.radiusMiles || 10}
                    onChange={(e) => handleFilterChange('radiusMiles', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <p className="text-sm text-gray-600">
                    Radius: {localFilters.radiusMiles || 10} miles
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">
                  No location selected
                </p>
              )}
            </div>
          </div>

          {/* Apply Button */}
          <div className="p-4 border-t">
            <button
              onClick={applyFilters}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={toggleSidebar}
        className={`fixed top-20 ${isSidebarOpen ? 'left-80' : 'left-0'} z-30 bg-white shadow-md rounded-r-md p-2 transition-all duration-300 hover:bg-gray-50`}
        aria-label="Toggle filters"
      >
        {isSidebarOpen ? (
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-600" />
        )}
      </button>
    </>
  );
};
