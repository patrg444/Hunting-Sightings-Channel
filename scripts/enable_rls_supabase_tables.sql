-- Enable Row Level Security on all Supabase tables
-- Run this in Supabase SQL Editor

-- 1. Enable RLS on all tables
ALTER TABLE public.geography_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.geometry_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gmus ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.google_review_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.google_reviews_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sightings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.spatial_ref_sys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trails ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wildlife_events ENABLE ROW LEVEL SECURITY;

-- 2. CRITICAL: Allow public read access to sightings (so your map works!)
CREATE POLICY "Allow public read access to sightings" ON public.sightings
    FOR SELECT
    USING (true);

-- 3. PostGIS system tables need public read access
CREATE POLICY "Allow public read access" ON public.spatial_ref_sys
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access" ON public.geography_columns
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access" ON public.geometry_columns
    FOR SELECT
    USING (true);

-- 4. GMUs and trails should be publicly readable for the map
CREATE POLICY "Allow public read access" ON public.gmus
    FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access" ON public.trails
    FOR SELECT
    USING (true);

-- 5. User-related tables - only accessible by authenticated users
CREATE POLICY "Users can read own data" ON public.users
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can read own preferences" ON public.user_preferences
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences" ON public.user_preferences
    FOR UPDATE
    USING (auth.uid() = user_id);

-- 6. Subscription tables - restricted to authenticated users
CREATE POLICY "Users can read own subscriptions" ON public.subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can read own user_subscriptions" ON public.user_subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- 7. Usage limits - only service role can modify
CREATE POLICY "Public can read usage limits" ON public.usage_limits
    FOR SELECT
    USING (true);

-- 8. Cache tables - service role only (for scrapers)
-- No policies means only service role can access

-- 9. Wildlife events - public read
CREATE POLICY "Allow public read access" ON public.wildlife_events
    FOR SELECT
    USING (true);

-- To allow your scrapers to insert sightings, they should use the service role key
-- The service role bypasses RLS, so no additional policies needed for inserts