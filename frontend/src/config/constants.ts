// API and service configuration
export const API_URL = import.meta.env.VITE_API_URL || '';
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

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