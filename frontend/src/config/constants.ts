// API and service configuration
export const API_URL = import.meta.env.VITE_API_URL || '';

// Supabase configuration
// Note: The anon key is safe to be public as it's meant for client-side usage
// Row Level Security (RLS) policies protect the actual data
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://rvrdbtrxwndeerqmziuo.supabase.co';
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmRidHJ4d25kZWVycW16aXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4NDY1NTcsImV4cCI6MjA2NjQyMjU1N30.ExvP-7mWzplSmkGnw0eiD_q9qnP8IAO48qBxXp0baAs';

// Validate configuration
if (!SUPABASE_URL || SUPABASE_URL === 'undefined') {
  console.error('SUPABASE_URL is not configured!');
}
if (!SUPABASE_ANON_KEY || SUPABASE_ANON_KEY === 'undefined') {
  console.error('SUPABASE_ANON_KEY is not configured!');
}

console.log('Config loaded:', {
  API_URL,
  SUPABASE_URL,
  SUPABASE_KEY_LENGTH: SUPABASE_ANON_KEY?.length || 0
});