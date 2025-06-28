import { MapContainer } from '../components/Map/MapContainer';
import { FilterSidebar } from '../components/Filters/FilterSidebar';
import { useStore } from '../store/store';

export function MapPage() {
  const { isSidebarOpen } = useStore();

  return (
    <div className="flex-1 flex relative overflow-hidden">
      {/* Filter Sidebar */}
      <div
        className={`
          absolute lg:relative z-20 h-full bg-white shadow-lg transition-all duration-300
          ${isSidebarOpen ? 'w-80' : 'w-0 lg:w-0'}
        `}
      >
        <FilterSidebar />
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer />
      </div>
    </div>
  );
}