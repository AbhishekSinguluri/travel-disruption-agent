import os
import re

app_path = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend\src\App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add new state variables for name and phone
if "const [name, setName] = useState('');" not in content:
    content = content.replace(
        "const [password, setPassword] = useState('');",
        "const [password, setPassword] = useState('');\n  const [name, setName] = useState('');\n  const [phone, setPhone] = useState('');"
    )

# Replace renderLogin
new_render_login = """
  const renderLogin = () => (
    <div className="min-h-screen flex items-center justify-center bg-[#F9F8F6] p-4 relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <img src="/roam_image_assets/destinations/destination_beach_aerial.png" className="w-full h-full object-cover opacity-20" alt="Background" />
      </div>
      <div className="bg-white p-10 rounded-[2rem] shadow-2xl max-w-md w-full z-10 relative">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-serif text-slate-900 tracking-tight mb-2">ROAM</h1>
          <p className="text-slate-500 font-light tracking-wide uppercase text-xs">Your Journeys</p>
        </div>
        
        {authError && <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-xl text-sm border border-red-100">{authError}</div>}
        
        <div className="space-y-4 mb-6">
          <input 
            type="text" 
            placeholder="Full Name (for signup)" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={name} 
            onChange={(e) => setName(e.target.value)} 
          />
          <input 
            type="email" 
            placeholder="Email address" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
          />
          <input 
            type="tel" 
            placeholder="Phone Number (for signup)" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={phone} 
            onChange={(e) => setPhone(e.target.value)} 
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="w-full p-4 bg-slate-50 border border-slate-100 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            onKeyDown={(e) => e.key === 'Enter' && login(email, password)}
          />
        </div>
        
        <div className="space-y-3">
          <button 
            onClick={() => { login(email, password); setCurrentView('TRIPS'); }} 
            disabled={loading || !email || !password} 
            className="w-full bg-slate-900 text-white py-4 rounded-xl font-bold tracking-wide hover:bg-slate-800 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
          
          <button 
            onClick={() => { signup(email, password); setCurrentView('TRIPS'); }} 
            disabled={loading || !email || !password || !name || !phone} 
            className="w-full bg-white text-slate-900 border border-slate-200 py-4 rounded-xl font-bold tracking-wide hover:bg-slate-50 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Create Account
          </button>
          
          <div className="relative flex py-4 items-center">
            <div className="flex-grow border-t border-slate-200"></div>
            <span className="flex-shrink-0 mx-4 text-slate-400 text-sm">or</span>
            <div className="flex-grow border-t border-slate-200"></div>
          </div>
          
          <button 
            onClick={() => { 
                fetch("http://localhost:8000/api/auth/google/login", { method: 'POST', body: JSON.stringify({mock: true}) })
                  .then(() => { setUser({ id: 'google-user', email: email || 'demo@gmail.com', name: name || 'Demo User' }); setCurrentView('TRIPS'); })
            }} 
            className="w-full bg-white text-slate-700 border border-slate-200 py-4 rounded-xl font-bold tracking-wide hover:bg-slate-50 transition-all shadow-sm flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>
          
          <button 
            onClick={() => { login('demo', 'demo'); setCurrentView('TRIPS'); }} 
            className="w-full mt-4 text-xs font-bold uppercase tracking-widest text-slate-400 hover:text-slate-600 transition-colors"
          >
            Continue in Demo Mode
          </button>
        </div>
      </div>
    </div>
  );
"""

# replace the old renderLogin function. It spans multiple lines, so we use regex.
content = re.sub(r'const renderLogin = \(\) => \(.*?\);\s*(?=const renderTrips)', new_render_login, content, flags=re.DOTALL)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Frontend Auth code generated.")
