import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

frontend_src = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src"

# Add AuthStore using Zustand
auth_store_content = """
import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isDemoMode: true, // Auto-fallback
  setUser: (user) => set({ user, isAuthenticated: !!user, isDemoMode: !user }),
  logout: () => set({ user: null, isAuthenticated: false, isDemoMode: true }),
}));
"""
write_file(f"{frontend_src}/store/authStore.js", auth_store_content)

# Setup basic Trips list UI and update App.jsx routing
app_jsx_path = f"{frontend_src}/App.jsx"
with open(app_jsx_path, 'r', encoding='utf-8') as f:
    app_jsx = f.read()

# I am going to wrap the existing return statement in a router-like state
if "useAuthStore" not in app_jsx:
    app_jsx = app_jsx.replace("import { useTripStore }", "import { useTripStore }\nimport { useAuthStore } from './store/authStore';")
    
    app_jsx = app_jsx.replace("export default function App() {", """
export default function App() {
  const { isDemoMode, isAuthenticated, user, setUser } = useAuthStore();
  const [currentView, setCurrentView] = useState('TRIPS'); // TRIPS, DASHBOARD, LOGIN

  if (!isAuthenticated && !isDemoMode && currentView !== 'LOGIN') {
      setCurrentView('LOGIN');
  }
""")

    # We inject a render map
    render_func = """
  const renderLogin = () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow-md w-96 text-center">
        <h2 className="text-2xl font-bold mb-4">Login to Trip Agent</h2>
        <p className="text-gray-500 mb-6">Supabase credentials not fully configured. Using DEMO MODE.</p>
        <button onClick={() => { setUser({id: 'demo-user', email: 'demo@example.com'}); setCurrentView('TRIPS'); }} className="w-full bg-blue-600 text-white py-2 rounded">
          Continue in Demo Mode
        </button>
      </div>
    </div>
  );

  const renderTrips = () => (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold">My Trips</h1>
            {isDemoMode && <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded font-bold text-sm">DEMO MODE</span>}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div onClick={() => setCurrentView('DASHBOARD')} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 cursor-pointer hover:border-blue-500 transition">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold">Hyderabad Weekend</h3>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">ACTIVE</span>
                </div>
                <p className="text-gray-500">Sep 25 - Sep 27</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 opacity-60">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold">Goa Trip</h3>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">PLANNING</span>
                </div>
                <p className="text-gray-500">Oct 10 - Oct 14</p>
            </div>
        </div>
      </div>
    </div>
  );

  if (currentView === 'LOGIN') return renderLogin();
  if (currentView === 'TRIPS') return renderTrips();
"""
    app_jsx = app_jsx.replace("const stops = trip.days[0].stops;", "const stops = trip.days[0].stops;\n" + render_func)

    # Wrap the original return in a dashboard render
    app_jsx = app_jsx.replace("return (", "return (\n    <div>\n    <button onClick={() => setCurrentView('TRIPS')} className=\"m-4 px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded\">&larr; Back to Trips</button>")
    app_jsx = app_jsx.replace("</div>\n    </div>\n  );\n}", "</div>\n    </div>\n    </div>\n  );\n}")
    
    write_file(app_jsx_path, app_jsx)
