import axios from 'axios';
import { supabase } from './auth';
import { API_URL } from '@/config/constants';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL ? `${API_URL}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, sign out
      await supabase.auth.signOut();
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
