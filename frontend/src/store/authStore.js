import { create } from 'zustand';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const supabase = (supabaseUrl && supabaseKey && supabaseUrl !== 'your_supabase_url_here')
  ? createClient(supabaseUrl, supabaseKey)
  : null;

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isDemoMode: !supabase, 
  loading: false,
  error: null,
  
  initialize: async () => {
    if (!supabase) return;
    const { data } = await supabase.auth.getSession();
    if (data.session) {
      set({ user: data.session.user, isAuthenticated: true });
    }
  },
  
  login: async (email, password) => {
    if (!supabase) {
        set({ user: { id: 'demo-user', email: 'demo@example.com' }, isAuthenticated: true, isDemoMode: true });
        return;
    }
    set({ loading: true, error: null });
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) set({ error: error.message, loading: false });
    else set({ user: data.user, isAuthenticated: true, loading: false });
  },
  
  signup: async (email, password) => {
    if (!supabase) return set({ error: 'Demo mode cannot sign up.' });
    set({ loading: true, error: null });
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) set({ error: error.message, loading: false });
    else set({ user: data.user, isAuthenticated: true, loading: false });
  },

  logout: async () => {
    if (supabase) await supabase.auth.signOut();
    set({ user: null, isAuthenticated: false });
  },
}));
