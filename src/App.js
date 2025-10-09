import React, { useState } from 'react';
import { User, Coffee, Sparkles } from 'lucide-react';
import Profile from './components/Profile';
import BeanCollection from './components/BeanCollection';
import RecipeGenerator from './components/RecipeGenerator';

function App() {
  const [activeTab, setActiveTab] = useState('profile');

  const renderContent = () => {
    switch (activeTab) {
      case 'profile':
        return <Profile />;
      case 'beans':
        return <BeanCollection />;
      case 'recipe':
        return <RecipeGenerator />;
      default:
        return <Profile />;
    }
  };

  return (
    <div className="w-full max-w-md mx-auto min-h-screen flex flex-col bg-gradient-to-b from-coffee-50 to-coffee-100">
      {/* Header */}
      <header className="bg-coffee-900 text-white p-4 shadow-lg">
        <h1 className="text-2xl font-bold text-center">☕ The Daily Drip</h1>
        <p className="text-center text-coffee-300 text-sm mt-1">Your Coffee Brewing Companion</p>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-20">
        {renderContent()}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-coffee-200 shadow-lg max-w-md mx-auto">
        <div className="flex justify-around items-center h-16">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
              activeTab === 'profile'
                ? 'text-coffee-900 bg-coffee-50'
                : 'text-coffee-400 hover:text-coffee-700'
            }`}
          >
            <User size={24} />
            <span className="text-xs mt-1">Profile</span>
          </button>
          <button
            onClick={() => setActiveTab('beans')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
              activeTab === 'beans'
                ? 'text-coffee-900 bg-coffee-50'
                : 'text-coffee-400 hover:text-coffee-700'
            }`}
          >
            <Coffee size={24} />
            <span className="text-xs mt-1">Beans</span>
          </button>
          <button
            onClick={() => setActiveTab('recipe')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
              activeTab === 'recipe'
                ? 'text-coffee-900 bg-coffee-50'
                : 'text-coffee-400 hover:text-coffee-700'
            }`}
          >
            <Sparkles size={24} />
            <span className="text-xs mt-1">Recipe</span>
          </button>
        </div>
      </nav>
    </div>
  );
}

export default App;
