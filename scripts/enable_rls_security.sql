-- Enable Row Level Security on all public tables
-- This prevents unauthorized access to your data

-- Enable RLS on sightings table
ALTER TABLE public.sightings ENABLE ROW LEVEL SECURITY;

-- Enable RLS on other tables
ALTER TABLE public.spatial_ref_sys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gmus ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.google_reviews_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wildlife_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.google_review_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trails ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access to sightings (if desired)
-- This allows anyone to read sightings but not modify them
CREATE POLICY "Allow public read access" ON public.sightings
    FOR SELECT
    TO public
    USING (true);

-- Create policy for authenticated users to insert sightings (optional)
-- CREATE POLICY "Allow authenticated insert" ON public.sightings
--     FOR INSERT
--     TO authenticated
--     WITH CHECK (true);

-- For spatial_ref_sys (PostGIS system table), allow public read
CREATE POLICY "Allow public read access" ON public.spatial_ref_sys
    FOR SELECT
    TO public
    USING (true);

-- For other tables, you may want more restrictive policies
-- Example: Only authenticated users can read
-- CREATE POLICY "Allow authenticated read" ON public.trails
--     FOR SELECT
--     TO authenticated
--     USING (true);