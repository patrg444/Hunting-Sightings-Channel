import React, { useState, useMemo } from 'react';
import { useStore } from '@/store/store';
import { format } from 'date-fns';
import { ExternalLink, Info, ChevronDown, ChevronUp, ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { deduplicateSightings, getDuplicateStats } from '@/utils/deduplicateSightings';

type SortField = 'date' | 'gmu' | 'species' | 'source';
type SortDirection = 'asc' | 'desc';

export const SightingsTable: React.FC = () => {
  const { sightings, totalSightings, currentPage, setCurrentPage, isLoading } = useStore();
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  
  const pageSize = 100;
  const totalPages = Math.ceil(totalSightings / pageSize);
  
  // Valid species list (lowercase for comparison)
  const validSpecies = [
    'bear', 'black bear', 'grizzly bear', 'brown bear',
    'elk', 
    'deer', 'white tail', 'whitetail', 'white-tailed deer', 'mule deer', 
    'moose', 
    'pronghorn', 'antelope', 'pronghorn antelope',
    'bighorn', 'bighorn sheep', 
    'mountain lion', 'cougar', 'puma',
    'mountain goat',
    'hog', 'wild hog', 'feral hog', 'wild boar',
    'marmot', 'yellow-bellied marmot'
  ];
  
  // Helper function to clean species names
  const cleanSpeciesName = (species: string | undefined): string => {
    if (!species) return 'Unknown';
    return species
      .replace(/_/g, ' ')  // Replace underscores with spaces
      .replace(/\([^)]*\)/g, '')  // Remove parentheses and content
      .trim()  // Remove extra whitespace
      .split(' ')  // Split into words
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())  // Capitalize each word
      .join(' ');
  };
  
  // Helper function to check if species is valid
  const isValidSpecies = (species: string | undefined): boolean => {
    if (!species) return false;
    const cleaned = species
      .replace(/_/g, ' ')
      .replace(/\([^)]*\)/g, '')
      .trim()
      .toLowerCase();
    return validSpecies.includes(cleaned);
  };
  

  const toggleRowExpansion = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Track deduplication stats
  const duplicateStats = useMemo(() => {
    return sightings.length > 0 ? getDuplicateStats(sightings) : null;
  }, [sightings]);

  const sortedSightings = useMemo(() => {
    // First deduplicate the sightings
    const deduplicatedSightings = deduplicateSightings(sightings);
    
    // Log duplicate stats in development
    if (process.env.NODE_ENV === 'development' && sightings.length > 0 && duplicateStats?.duplicateCount) {
      console.log('Duplicate stats:', duplicateStats);
    }
    
    // Then filter out invalid species
    const validSightings = deduplicatedSightings.filter(sighting => isValidSpecies(sighting.species));
    
    const sorted = [...validSightings].sort((a, b) => {
      let aVal, bVal;
      
      switch (sortField) {
        case 'date':
          aVal = a.sighting_date || a.date || '';
          bVal = b.sighting_date || b.date || '';
          break;
        case 'gmu':
          aVal = a.gmu_unit || a.gmu || 0;
          bVal = b.gmu_unit || b.gmu || 0;
          break;
        case 'species':
          aVal = a.species || '';
          bVal = b.species || '';
          break;
        case 'source':
          aVal = a.source_type || a.source || '';
          bVal = b.source_type || b.source || '';
          break;
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    
    return sorted;
  }, [sightings, sortField, sortDirection]);

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 ml-1 opacity-50" />;
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="w-3 h-3 ml-1" />
      : <ArrowDown className="w-3 h-3 ml-1" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading sightings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-white dark:bg-gray-900">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10 select-none">
          <tr>
            <th className="pl-8 pr-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <button
                onClick={() => handleSort('date')}
                className="flex items-center hover:text-gray-700 dark:hover:text-gray-200"
              >
                Date
                <SortIcon field="date" />
              </button>
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <button
                onClick={() => handleSort('gmu')}
                className="flex items-center hover:text-gray-700 dark:hover:text-gray-200"
              >
                GMU
                <SortIcon field="gmu" />
              </button>
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <button
                onClick={() => handleSort('species')}
                className="flex items-center hover:text-gray-700 dark:hover:text-gray-200"
              >
                Species
                <SortIcon field="species" />
              </button>
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <button
                onClick={() => handleSort('source')}
                className="flex items-center hover:text-gray-700 dark:hover:text-gray-200"
              >
                Source
                <SortIcon field="source" />
              </button>
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Sighting Link
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Coordinates
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {sortedSightings.map((sighting) => (
            <React.Fragment key={sighting.id}>
              <tr 
                className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer select-none"
                onClick={() => toggleRowExpansion(sighting.id)}
              >
                <td className="pl-8 pr-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {sighting.sighting_date || sighting.date
                    ? format(new Date((sighting.sighting_date || sighting.date) + 'T12:00:00'), 'MMM dd, yyyy')
                    : 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {sighting.gmu_unit || sighting.gmu || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {cleanSpeciesName(sighting.species)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {sighting.source_type || sighting.source || 'Unknown'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                  {sighting.source_url || sighting.url ? (
                    <a
                      href={sighting.source_url || sighting.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      Link
                    </a>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                  {(sighting.location?.lat && sighting.location?.lon) || (sighting.lat && sighting.lon) ? (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        toggleRowExpansion(sighting.id);
                      }}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800 transition-colors"
                    >
                      <Info className="w-3 h-3 mr-1" />
                      {expandedRows.has(sighting.id) ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )}
                    </button>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
              {expandedRows.has(sighting.id) && (
                <tr className="bg-gray-50 dark:bg-gray-800 select-none">
                  <td colSpan={6} className="px-6 py-4">
                    <div className="space-y-2">
                      <div className="text-sm">
                        <span className="font-medium text-gray-700 dark:text-gray-300">Coordinates: </span>
                        <span className="text-gray-600 dark:text-gray-400">
                          {sighting.location?.lat && sighting.location?.lon 
                            ? `${sighting.location.lat.toFixed(6)}, ${sighting.location.lon.toFixed(6)}`
                            : sighting.lat && sighting.lon
                            ? `${sighting.lat.toFixed(6)}, ${sighting.lon.toFixed(6)}`
                            : 'Not available'}
                        </span>
                      </div>
                      {sighting.location_name && (
                        <div className="text-sm">
                          <span className="font-medium text-gray-700 dark:text-gray-300">Location Name: </span>
                          <span className="text-gray-600 dark:text-gray-400">{sighting.location_name}</span>
                        </div>
                      )}
                      {sighting.location_confidence_radius && (
                        <div className="text-sm">
                          <span className="font-medium text-gray-700 dark:text-gray-300">Location Radius: </span>
                          <span className="text-gray-600 dark:text-gray-400">{sighting.location_confidence_radius} miles</span>
                        </div>
                      )}
                      <div className="text-sm">
                        <span className="font-medium text-gray-700 dark:text-gray-300">Sighting Text: </span>
                        <div className="mt-1 text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                          {sighting.raw_text || sighting.description || 'No description available'}
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
      {sightings.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">No sightings found</p>
        </div>
      )}
      
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white dark:bg-gray-900 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to{' '}
                <span className="font-medium">{Math.min(currentPage * pageSize, totalSightings)}</span> of{' '}
                <span className="font-medium">{totalSightings}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={i}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        currentPage === pageNum
                          ? 'z-10 bg-green-50 dark:bg-green-900 border-green-500 text-green-600 dark:text-green-400'
                          : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};