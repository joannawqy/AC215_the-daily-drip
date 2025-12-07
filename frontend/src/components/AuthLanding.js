import React, { useMemo, useState } from 'react';
import { Sparkles, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const INITIAL_STATE = {
  email: '',
  password: '',
  displayName: '',
  flavorNotes: '',
  roastLevel: '',
};

function parseFlavorNotes(value) {
  return value
    .split(',')
    .map((note) => note.trim())
    .filter(Boolean);
}

function AuthLanding() {
  const { login, register, authLoading, error, clearError } = useAuth();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState(INITIAL_STATE);

  const isLogin = mode === 'login';

  const formTitle = useMemo(
    () => (isLogin ? 'Sign in to Daily Drip' : 'Create your account'),
    [isLogin],
  );

  const toggleMode = () => {
    clearError();
    setMode(isLogin ? 'register' : 'login');
    setForm(INITIAL_STATE);
  };

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    clearError();
    try {
      if (isLogin) {
        await login({ email: form.email, password: form.password });
        return;
      }
      await register({
        email: form.email,
        password: form.password,
        display_name: form.displayName || undefined,
        preferences: {
          flavor_notes: parseFlavorNotes(form.flavorNotes),
          roast_level: form.roastLevel || null,
        },
      });
    } catch (err) {
      // Error is surfaced through context state.
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="bg-white/80 backdrop-blur-lg shadow-soft rounded-3xl max-w-4xl w-full grid lg:grid-cols-2 overflow-hidden border border-white/50 animate-fadeIn">
        <div className="bg-gradient-to-br from-coffee-900 to-coffee-800 text-white p-12 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1497935586351-b67a49e012bf?auto=format&fit=crop&q=80')] opacity-10 bg-cover bg-center mix-blend-overlay"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-cream-500 flex items-center justify-center text-white shadow-glow">
                <Sparkles size={20} />
              </div>
              <h1 className="text-2xl font-bold tracking-tight">The Daily Drip</h1>
            </div>
            <h2 className="text-4xl font-bold mb-6 leading-tight">
              Brew the perfect cup, <br />
              <span className="text-cream-300">every single time.</span>
            </h2>
            <p className="text-coffee-100 leading-relaxed text-lg">
              Your personal AI coffee companion. Track beans, discover recipes, and master the art of pour-over.
            </p>
          </div>
          <div className="relative z-10 mt-12">
            <div className="flex items-center gap-4 text-coffee-200 text-sm font-medium">
              <div className="flex -space-x-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full bg-coffee-700 border-2 border-coffee-800 flex items-center justify-center text-xs">
                    <UserPlus size={12} />
                  </div>
                ))}
              </div>
              <span>Join thousands of coffee lovers</span>
            </div>
          </div>
        </div>

        <div className="p-12 bg-white/50">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-coffee-900">{formTitle}</h2>
              <p className="text-coffee-600 mt-1">
                {isLogin ? 'Welcome back, brewer!' : 'Start your coffee journey today.'}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1.5">Email</label>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={handleChange('email')}
                  className="w-full bg-white border border-coffee-200 rounded-xl px-4 py-3 focus:outline-none focus:border-coffee-500 focus:ring-2 focus:ring-coffee-500/20 text-coffee-900 transition-all placeholder:text-coffee-300"
                  placeholder="hello@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1.5">Password</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={form.password}
                  onChange={handleChange('password')}
                  className="w-full bg-white border border-coffee-200 rounded-xl px-4 py-3 focus:outline-none focus:border-coffee-500 focus:ring-2 focus:ring-coffee-500/20 text-coffee-900 transition-all placeholder:text-coffee-300"
                  placeholder="••••••••"
                />
                {!isLogin && <p className="text-xs text-coffee-500 mt-1.5">Must be at least 6 characters</p>}
              </div>

              {!isLogin && (
                <div className="space-y-4 animate-slideUp">
                  <div>
                    <label className="block text-sm font-semibold text-coffee-700 mb-1.5">
                      Display Name <span className="text-coffee-400 font-normal">(Optional)</span>
                    </label>
                    <input
                      type="text"
                      value={form.displayName}
                      onChange={handleChange('displayName')}
                      className="w-full bg-white border border-coffee-200 rounded-xl px-4 py-3 focus:outline-none focus:border-coffee-500 focus:ring-2 focus:ring-coffee-500/20 text-coffee-900 transition-all placeholder:text-coffee-300"
                      placeholder="Barista Bob"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-coffee-700 mb-1.5">
                        Flavor Notes
                      </label>
                      <input
                        type="text"
                        value={form.flavorNotes}
                        onChange={handleChange('flavorNotes')}
                        placeholder="Fruity, Nutty"
                        className="w-full bg-white border border-coffee-200 rounded-xl px-4 py-3 focus:outline-none focus:border-coffee-500 focus:ring-2 focus:ring-coffee-500/20 text-coffee-900 transition-all placeholder:text-coffee-300"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-coffee-700 mb-1.5">
                        Roast Level
                      </label>
                      <input
                        type="text"
                        value={form.roastLevel}
                        onChange={handleChange('roastLevel')}
                        placeholder="Medium"
                        className="w-full bg-white border border-coffee-200 rounded-xl px-4 py-3 focus:outline-none focus:border-coffee-500 focus:ring-2 focus:ring-coffee-500/20 text-coffee-900 transition-all placeholder:text-coffee-300"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-xl px-4 py-3 animate-fadeIn">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={authLoading}
              className={`w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold text-white shadow-lg shadow-coffee-500/20 transition-all transform active:scale-[0.98] ${authLoading
                ? 'bg-coffee-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-coffee-600 to-coffee-500 hover:from-coffee-700 hover:to-coffee-600 hover:shadow-coffee-500/30'
                }`}
            >
              {authLoading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  {!isLogin && <UserPlus size={18} />}
                </>
              )}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={toggleMode}
                className="text-sm font-medium text-coffee-600 hover:text-coffee-800 transition-colors"
              >
                {isLogin ? (
                  <>New to Daily Drip? <span className="text-coffee-700 font-bold hover:underline">Create an account</span></>
                ) : (
                  <>Already have an account? <span className="text-coffee-700 font-bold hover:underline">Sign in</span></>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AuthLanding;
