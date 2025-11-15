import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Coffee, LogOut, PenSquare, Sparkles, User as UserIcon } from 'lucide-react';
import Profile from './components/Profile';
import BeanCollection from './components/BeanCollection';
import RecipeGenerator from './components/RecipeGenerator';
import AuthLanding from './components/AuthLanding';
import { AuthProvider, useAuth } from './context/AuthContext';
import {
  createBean,
  deleteBean,
  listBeans,
  updateBean,
  updatePreferences,
} from './services/agentClient';

function AppShell() {
  const { user, initializing, logout, refreshProfile } = useAuth();
  const [activeSection, setActiveSection] = useState('recipe');
  const [beans, setBeans] = useState([]);
  const [beansLoading, setBeansLoading] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);

  const loadBeans = useCallback(async () => {
    if (!user) {
      setBeans([]);
      return;
    }
    setBeansLoading(true);
    try {
      const data = await listBeans();
      setBeans(data.beans || []);
    } catch (err) {
      console.error('Failed to load beans', err);
    } finally {
      setBeansLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadBeans();
  }, [loadBeans]);

  const handlePreferencesSave = useCallback(
    async (preferences) => {
      setSavingPreferences(true);
      try {
        await updatePreferences(preferences);
        await refreshProfile();
      } finally {
        setSavingPreferences(false);
      }
    },
    [refreshProfile],
  );

  const handleCreateBean = useCallback(
    async (bean) => {
      const record = await createBean({ bean });
      setBeans((prev) => [...prev, record]);
      return record;
    },
    [],
  );

  const handleUpdateBean = useCallback(
    async (beanId, bean) => {
      const record = await updateBean(beanId, { bean });
      setBeans((prev) => prev.map((entry) => (entry.bean_id === beanId ? record : entry)));
      return record;
    },
    [],
  );

  const handleDeleteBean = useCallback(
    async (beanId) => {
      await deleteBean(beanId);
      setBeans((prev) => prev.filter((entry) => entry.bean_id !== beanId));
    },
    [],
  );

  const navigation = useMemo(
    () => [
      { id: 'profile', label: 'Profile', icon: <UserIcon size={18} /> },
      { id: 'beans', label: 'Bean Library', icon: <Coffee size={18} /> },
      { id: 'recipe', label: 'Recipe Studio', icon: <Sparkles size={18} /> },
    ],
    [],
  );

  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-coffee-50 to-coffee-100">
        <div className="bg-white px-6 py-4 rounded-xl shadow-md text-coffee-700">
          Loading Daily Drip…
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthLanding />;
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'profile':
        return (
          <Profile
            user={user}
            onSavePreferences={handlePreferencesSave}
            saving={savingPreferences}
          />
        );
      case 'beans':
        return (
          <BeanCollection
            beans={beans}
            loading={beansLoading}
            onCreate={handleCreateBean}
            onUpdate={handleUpdateBean}
            onDelete={handleDeleteBean}
          />
        );
      case 'recipe':
      default:
        return <RecipeGenerator beans={beans} onRefreshBeans={loadBeans} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-coffee-50 to-coffee-100">
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-coffee-900 flex items-center gap-2">
              ☕ The Daily Drip
            </h1>
            <p className="text-coffee-600">Brew smarter, track better, savor more.</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-coffee-900 font-semibold">{user.display_name || user.email}</p>
              <p className="text-coffee-500 text-sm">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-coffee-200 text-coffee-700 hover:bg-coffee-100 transition-colors"
            >
              <LogOut size={18} />
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-[240px,1fr]">
          <aside className="bg-white rounded-2xl shadow-sm border border-coffee-100 p-4">
            <nav className="space-y-2">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors ${
                    activeSection === item.id
                      ? 'bg-coffee-700 text-white shadow-md'
                      : 'text-coffee-700 hover:bg-coffee-100'
                  }`}
                >
                  {item.icon}
                  <span className="font-semibold">{item.label}</span>
                </button>
              ))}
              <div className="mt-6 p-4 rounded-xl bg-coffee-50 border border-dashed border-coffee-200">
                <div className="flex items-start gap-2 text-sm text-coffee-700">
                  <PenSquare size={16} className="mt-0.5 text-coffee-600" />
                  <span>Brew recipes are tailored to your saved beans or manual entries.</span>
                </div>
              </div>
            </nav>
          </aside>
          <section className="space-y-6">{renderSection()}</section>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}

export default App;
