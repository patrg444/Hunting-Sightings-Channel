import { createClient } from '@supabase/supabase-js';
import type { User, LoginCredentials, SignupCredentials } from '@/types';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@/config/constants';

// Initialize Supabase client with error handling
let supabase: any;
try {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY || SUPABASE_URL === 'undefined' || SUPABASE_ANON_KEY === 'undefined') {
    throw new Error('Supabase configuration is missing');
  }
  supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
} catch (error) {
  console.error('Failed to initialize Supabase client:', error);
  // Create a mock client that returns errors
  supabase = {
    auth: {
      signInWithPassword: async () => ({ data: null, error: new Error('Supabase not configured') }),
      signUp: async () => ({ data: null, error: new Error('Supabase not configured') }),
      signOut: async () => ({ error: new Error('Supabase not configured') }),
      getSession: async () => ({ data: { session: null }, error: null }),
      getUser: async () => ({ data: { user: null }, error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } })
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          gte: () => ({
            lte: () => ({
              order: () => ({
                limit: () => ({ data: [], error: null, count: 0 })
              })
            })
          })
        })
      })
    })
  };
}

export { supabase };

// Auth service methods
export const authService = {
  // Login with email and password
  async login({ email, password }: LoginCredentials) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) throw error;
    return data;
  },

  // Sign up new user
  async signup({ email, password }: SignupCredentials) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });
    
    if (error) throw error;
    return data;
  },

  // Logout
  async logout() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  // Get current user
  async getCurrentUser(): Promise<User | null> {
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) return null;
    
    return {
      id: user.id,
      email: user.email!,
      created_at: user.created_at,
    };
  },

  // Reset password
  async resetPassword(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    
    if (error) throw error;
  },

  // Update password
  async updatePassword(newPassword: string) {
    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    });
    
    if (error) throw error;
  },

  // Subscribe to auth state changes
  onAuthStateChange(callback: (user: User | null) => void) {
    return supabase.auth.onAuthStateChange(async (_, session) => {
      if (session?.user) {
        callback({
          id: session.user.id,
          email: session.user.email!,
          created_at: session.user.created_at,
        });
      } else {
        callback(null);
      }
    });
  },
};
