import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# Add Supabase client and update AuthStore
auth_store_content = """
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
"""
write_file(f"{frontend_src}/store/authStore.js", auth_store_content)

# Update App.jsx to include the fully working auth UI
app_jsx_path = f"{frontend_src}/App.jsx"
with open(app_jsx_path, 'r', encoding='utf-8') as f:
    app_jsx = f.read()

# Replace dummy renderLogin and renderTrips with robust ones
app_jsx = app_jsx.replace("const renderLogin = () => (", """
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, signup, loading, error, logout } = useAuthStore();
  
  const renderLogin = () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow-md w-96 text-center">
        <h2 className="text-2xl font-bold mb-4">Login to Trip Agent</h2>
        
        {isDemoMode ? (
            <div className="mb-4">
                <p className="text-orange-600 mb-6 font-bold bg-orange-100 p-2 rounded">DEMO MODE ENABLED</p>
                <p className="text-gray-500 mb-6 text-sm">Supabase credentials not fully configured.</p>
                <button onClick={() => { login('demo', 'demo'); setCurrentView('TRIPS'); }} className="w-full bg-blue-600 text-white py-2 rounded">
                  Continue in Demo Mode
                </button>
            </div>
        ) : (
            <div className="space-y-4">
                {error && <p className="text-red-500 text-sm">{error}</p>}
                <input className="w-full border p-2 rounded" type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
                <input className="w-full border p-2 rounded" type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} />
                <button onClick={() => { login(email, password); setCurrentView('TRIPS'); }} disabled={loading} className="w-full bg-blue-600 text-white py-2 rounded">
                    {loading ? 'Processing...' : 'Log In'}
                </button>
                <button onClick={() => { signup(email, password); setCurrentView('TRIPS'); }} disabled={loading} className="w-full bg-gray-600 text-white py-2 rounded">
                    Sign Up
                </button>
            </div>
        )}
      </div>
    </div>
  );
  
  const renderTripsDummy = () => (
""")

# Fix renderTrips wrapper
app_jsx = app_jsx.replace("const renderTrips = () => (", "const renderTrips = () => (\n")
app_jsx = app_jsx.replace("DEMO MODE</span>}", "DEMO MODE</span>}\n            {!isDemoMode && <span className=\"bg-green-100 text-green-800 px-3 py-1 rounded font-bold text-sm\">LIVE MODE</span>}\n            <button onClick={() => { logout(); setCurrentView('LOGIN'); }} className=\"ml-4 text-sm underline text-gray-500\">Logout</button>")

write_file(app_jsx_path, app_jsx)
