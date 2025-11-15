import React, { useEffect, useMemo, useState } from 'react';
import { Coffee, Droplet } from 'lucide-react';

function formatNotes(notes) {
  return Array.isArray(notes) ? notes.join(', ') : '';
}

const defaultPreferences = {
  flavor_notes: [],
  roast_level: '',
};

function Profile({ user, onSavePreferences, saving }) {
  const preferences = user.preferences || defaultPreferences;
  const [flavorNotes, setFlavorNotes] = useState(formatNotes(preferences.flavor_notes));
  const [roastLevel, setRoastLevel] = useState(preferences.roast_level || '');

  useEffect(() => {
    setFlavorNotes(formatNotes(preferences.flavor_notes));
    setRoastLevel(preferences.roast_level || '');
  }, [preferences]);

  const beanCount = useMemo(() => user.beans?.length || 0, [user.beans]);

  const handleSubmit = (event) => {
    event.preventDefault();
    const payload = {
      flavor_notes: flavorNotes
        .split(',')
        .map((note) => note.trim())
        .filter(Boolean),
      roast_level: roastLevel || null,
    };
    onSavePreferences(payload);
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-2xl shadow-sm border border-coffee-100 p-6">
        <h2 className="text-2xl font-bold text-coffee-900 mb-2">Account Overview</h2>
        <p className="text-coffee-600 mb-4">
          Keep your taste profile focused. Flavor notes and roast level guide the agent during
          recipe generation.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-coffee-50 rounded-xl p-4 border border-coffee-100">
            <p className="text-sm text-coffee-600">Display name</p>
            <p className="text-lg font-semibold text-coffee-900 mt-1">
              {user.display_name || 'Not set'}
            </p>
          </div>
          <div className="bg-coffee-50 rounded-xl p-4 border border-coffee-100">
            <p className="text-sm text-coffee-600">Email</p>
            <p className="text-lg font-semibold text-coffee-900 mt-1">{user.email}</p>
          </div>
          <div className="bg-coffee-50 rounded-xl p-4 border border-coffee-100 flex items-center gap-3">
            <Coffee className="text-coffee-700" size={24} />
            <div>
              <p className="text-sm text-coffee-600">Saved beans</p>
              <p className="text-lg font-semibold text-coffee-900 mt-1">{beanCount}</p>
            </div>
          </div>
          <div className="bg-coffee-50 rounded-xl p-4 border border-coffee-100 flex items-center gap-3">
            <Droplet className="text-coffee-700" size={24} />
            <div>
              <p className="text-sm text-coffee-600">Brew style</p>
              <p className="text-lg font-semibold text-coffee-900 mt-1">
                {roastLevel || 'Tell us your roast preference'}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-coffee-100 p-6">
        <h3 className="text-xl font-semibold text-coffee-900 mb-4">Coffee Preferences</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-coffee-700 mb-1">
              Favorite flavor notes
            </label>
            <textarea
              value={flavorNotes}
              onChange={(event) => setFlavorNotes(event.target.value)}
              rows={3}
              placeholder="citrus, stone fruit, caramel"
              className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900 resize-y"
            />
            <p className="text-xs text-coffee-500 mt-1">
              Separate notes with commas. These shape the agent&apos;s flavor emphasis.
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-coffee-700 mb-1">
              Preferred roast level
            </label>
            <input
              type="text"
              value={roastLevel}
              onChange={(event) => setRoastLevel(event.target.value)}
              placeholder="Light, Medium, Light-Medium…"
              className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className={`inline-flex items-center gap-2 px-5 py-3 rounded-lg font-semibold text-white transition-colors ${
              saving ? 'bg-coffee-400 cursor-not-allowed' : 'bg-coffee-700 hover:bg-coffee-800'
            }`}
          >
            {saving ? 'Saving…' : 'Save preferences'}
          </button>
        </form>
      </section>
    </div>
  );
}

export default Profile;
