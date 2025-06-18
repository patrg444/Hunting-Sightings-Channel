# Hunting Sightings Channel - Frontend

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Environment Variables
Copy `.env.example` to `.env` and update with your actual values:
```bash
cp .env.example .env
```

Required environment variables:
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key

### 3. Start the Backend Server
The backend API must be running on port 8000. Open a new terminal and run:
```bash
# From the project root directory
cd /Users/patrickgloria/Hunting-Sightings-Channel/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or if you're currently in the frontend directory:
```bash
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start the Frontend Development Server
In a new terminal:
```bash
npm run dev
```

The application will be available at http://localhost:5173

## Features

### Interactive Map
- Leaflet-based map centered on Colorado
- GMU (Game Management Unit) polygon overlays
- Wildlife sighting markers with clustering
- Click on markers for detailed information

### Filter Sidebar
- Filter by GMU number
- Filter by species (Elk, Deer, Bear, etc.)
- Filter by data source
- Date range filtering
- Location-based radius search

### Responsive Design
- Mobile-friendly layout
- Collapsible sidebar
- Touch-optimized controls

## Project Structure
```
src/
├── components/
│   ├── Map/
│   │   ├── MapContainer.tsx    # Main map component
│   │   ├── GMULayer.tsx        # GMU polygon layer
│   │   └── SightingClusters.tsx # Marker clustering
│   ├── Filters/
│   │   └── FilterSidebar.tsx   # Filter controls
│   └── Layout/
│       ├── Header.tsx          # Navigation header
│       └── LoadingSpinner.tsx  # Loading indicator
├── services/
│   ├── api.ts                  # Axios configuration
│   ├── auth.ts                 # Supabase auth
│   └── sightings.ts            # Sightings API
├── store/
│   └── store.ts                # Zustand state management
└── types/
    └── index.ts                # TypeScript definitions
```

## Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Technologies Used
- React 18 with TypeScript
- Vite for fast builds
- Leaflet & react-leaflet for maps
- Tailwind CSS for styling
- Zustand for state management
- Axios for API calls
- Supabase for authentication
