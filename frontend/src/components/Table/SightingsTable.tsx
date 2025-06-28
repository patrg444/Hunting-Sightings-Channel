import React, { useState } from 'react';
import { useStore } from '@/store/store';
import { format } from 'date-fns';
import { ExternalLink, Info, ChevronDown, ChevronUp } from 'lucide-react';

export const SightingsTable: React.FC = () => {
  const { sightings } = useStore();
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const toggleRowExpansion = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  return (
    <div className="h-full overflow-auto bg-white dark:bg-gray-900">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Date
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              GMU
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Species
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Source
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
          {sightings.map((sighting) => (
            <React.Fragment key={sighting.id}>
              <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {sighting.date 
                    ? format(new Date(sighting.date), 'MMM dd, yyyy')
                    : 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {sighting.gmu || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {sighting.species || 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                    {sighting.source || 'Unknown'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-center">
                  {sighting.url ? (
                    <a
                      href={sighting.url}
                      target="_blank"
                      rel="noopener noreferrer"
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
                  {sighting.lat && sighting.lon ? (
                    <button
                      onClick={() => toggleRowExpansion(sighting.id)}
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
                <tr className="bg-gray-50 dark:bg-gray-800">
                  <td colSpan={6} className="px-6 py-4">
                    <div className="space-y-2">
                      <div className="text-sm">
                        <span className="font-medium text-gray-700 dark:text-gray-300">Coordinates: </span>
                        <span className="text-gray-600 dark:text-gray-400">
                          {sighting.lat && sighting.lon 
                            ? `${sighting.lat.toFixed(6)}, ${sighting.lon.toFixed(6)}`
                            : 'Not available'}
                        </span>
                      </div>
                      {sighting.location && (
                        <div className="text-sm">
                          <span className="font-medium text-gray-700 dark:text-gray-300">Location: </span>
                          <span className="text-gray-600 dark:text-gray-400">{sighting.location}</span>
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
    </div>
  );
};