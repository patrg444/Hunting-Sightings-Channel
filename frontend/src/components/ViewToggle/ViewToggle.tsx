import React from 'react';
import { Map, Table } from 'lucide-react';
import { useStore } from '@/store/store';

export const ViewToggle: React.FC = () => {
  const { viewMode, setViewMode } = useStore();

  return (
    <div className="absolute top-4 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-md p-1 flex">
      <button
        onClick={() => setViewMode('map')}
        className={`px-3 py-2 rounded-md flex items-center gap-2 transition-colors ${
          viewMode === 'map'
            ? 'bg-green-600 text-white'
            : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
        }`}
        aria-label="Map view"
      >
        <Map className="w-4 h-4" />
        <span className="text-sm font-medium">Map</span>
      </button>
      <button
        onClick={() => setViewMode('table')}
        className={`px-3 py-2 rounded-md flex items-center gap-2 transition-colors ${
          viewMode === 'table'
            ? 'bg-green-600 text-white'
            : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
        }`}
        aria-label="Table view"
      >
        <Table className="w-4 h-4" />
        <span className="text-sm font-medium">Table</span>
      </button>
    </div>
  );
};