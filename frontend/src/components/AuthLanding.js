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
    <div className="min-h-screen bg-gradient-to-br from-coffee-50 to-coffee-100 flex items-center justify-center px-4">
      <div className="bg-white shadow-xl rounded-3xl max-w-2xl w-full grid lg:grid-cols-2 overflow-hidden">
        <div className="bg-coffee-800 text-white p-8 flex flex-col justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-4">The Daily Drip</h1>
            <p className="text-coffee-100 leading-relaxed">
              Build your personalized bean library, capture flavor preferences, and let the agent
              craft pour-over recipes tailored to every brew session.
            </p>
          </div>
          <div className="mt-8">
            <div className="flex items-center gap-2 text-coffee-100">
              <Sparkles size={18} />
              <span>Track beans, brew smarter, share great cups.</span>
            </div>
          </div>
        </div>

        <div className="p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-coffee-900">{formTitle}</h2>
              <p className="text-sm text-coffee-600">
                {isLogin ? 'Welcome back! ' : 'Join our brew circle.'}
              </p>
            </div>
            <button
              onClick={toggleMode}
              className="text-sm text-coffee-600 hover:text-coffee-900 transition-colors"
            >
              {isLogin ? 'Need an account?' : 'Already registered?'}
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-coffee-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={handleChange('email')}
                className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-coffee-700 mb-1">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={form.password}
                onChange={handleChange('password')}
                className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
              />
              <p className="text-xs text-coffee-500 mt-1">Minimum 6 characters.</p>
            </div>

            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-coffee-700 mb-1">
                    Display name (optional)
                  </label>
                  <input
                    type="text"
                    value={form.displayName}
                    onChange={handleChange('displayName')}
                    className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-coffee-700 mb-1">
                    Favorite flavor notes
                  </label>
                  <input
                    type="text"
                    value={form.flavorNotes}
                    onChange={handleChange('flavorNotes')}
                    placeholder="citrus, floral, cocoa"
                    className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                  />
                  <p className="text-xs text-coffee-500 mt-1">
                    Separate multiple notes with commas.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-coffee-700 mb-1">
                    Preferred roast level
                  </label>
                  <input
                    type="text"
                    value={form.roastLevel}
                    onChange={handleChange('roastLevel')}
                    placeholder="Light, Medium, etc."
                    className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                  />
                </div>
              </>
            )}

            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={authLoading}
              className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-white transition-colors ${
                authLoading ? 'bg-coffee-400 cursor-not-allowed' : 'bg-coffee-700 hover:bg-coffee-800'
              }`}
            >
              {isLogin ? 'Sign in' : 'Create account'}
              {!isLogin && <UserPlus size={16} />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AuthLanding;
