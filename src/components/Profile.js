import React from 'react';
import { User, Heart, Droplet, Thermometer } from 'lucide-react';

const Profile = () => {
  const userProfile = {
    name: 'Alex Chen',
    email: 'alex@coffee.lover',
    avatar: '👤',
    preferences: {
      brewStrength: 'Medium-Strong',
      flavorNotes: ['Chocolate', 'Nutty', 'Caramel'],
      preferredMethods: ['Pour Over', 'French Press', 'Aeropress'],
      temperature: '195-205°F',
      grindSize: 'Medium-Fine'
    },
    stats: {
      recipesGenerated: 47,
      beansOwned: 5,
      favoriteBean: 'Ethiopian Yirgacheffe'
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* User Info Card */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-20 h-20 bg-coffee-700 rounded-full flex items-center justify-center text-4xl">
            {userProfile.avatar}
          </div>
          <div>
            <h2 className="text-2xl font-bold text-coffee-900">{userProfile.name}</h2>
            <p className="text-coffee-600 text-sm">{userProfile.email}</p>
          </div>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-coffee-100">
          <div className="text-center">
            <p className="text-2xl font-bold text-coffee-900">{userProfile.stats.recipesGenerated}</p>
            <p className="text-xs text-coffee-600">Recipes</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-coffee-900">{userProfile.stats.beansOwned}</p>
            <p className="text-xs text-coffee-600">Beans</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-coffee-900">⭐</p>
            <p className="text-xs text-coffee-600">Enthusiast</p>
          </div>
        </div>
      </div>

      {/* Preferences Card */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <h3 className="text-lg font-bold text-coffee-900 mb-4 flex items-center">
          <Heart className="mr-2 text-coffee-700" size={20} />
          Coffee Preferences
        </h3>

        <div className="space-y-4">
          {/* Brew Strength */}
          <div>
            <div className="flex items-center mb-2">
              <Droplet className="mr-2 text-coffee-600" size={16} />
              <span className="text-sm font-semibold text-coffee-800">Brew Strength</span>
            </div>
            <div className="bg-coffee-50 rounded-lg p-3">
              <p className="text-coffee-900 font-medium">{userProfile.preferences.brewStrength}</p>
            </div>
          </div>

          {/* Flavor Notes */}
          <div>
            <div className="flex items-center mb-2">
              <span className="text-sm font-semibold text-coffee-800">Favorite Flavor Notes</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {userProfile.preferences.flavorNotes.map((note, index) => (
                <span
                  key={index}
                  className="bg-coffee-700 text-white px-3 py-1 rounded-full text-sm"
                >
                  {note}
                </span>
              ))}
            </div>
          </div>

          {/* Preferred Methods */}
          <div>
            <div className="flex items-center mb-2">
              <span className="text-sm font-semibold text-coffee-800">Preferred Methods</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {userProfile.preferences.preferredMethods.map((method, index) => (
                <span
                  key={index}
                  className="bg-coffee-100 text-coffee-900 px-3 py-1 rounded-lg text-sm border border-coffee-300"
                >
                  {method}
                </span>
              ))}
            </div>
          </div>

          {/* Temperature */}
          <div>
            <div className="flex items-center mb-2">
              <Thermometer className="mr-2 text-coffee-600" size={16} />
              <span className="text-sm font-semibold text-coffee-800">Preferred Temperature</span>
            </div>
            <div className="bg-coffee-50 rounded-lg p-3">
              <p className="text-coffee-900 font-medium">{userProfile.preferences.temperature}</p>
            </div>
          </div>

          {/* Grind Size */}
          <div>
            <div className="flex items-center mb-2">
              <span className="text-sm font-semibold text-coffee-800">Grind Size</span>
            </div>
            <div className="bg-coffee-50 rounded-lg p-3">
              <p className="text-coffee-900 font-medium">{userProfile.preferences.grindSize}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Favorite Bean */}
      <div className="bg-gradient-to-r from-coffee-700 to-coffee-800 rounded-2xl shadow-md p-6 text-white">
        <h3 className="text-sm font-semibold mb-2 opacity-90">Current Favorite</h3>
        <p className="text-xl font-bold">☕ {userProfile.stats.favoriteBean}</p>
      </div>
    </div>
  );
};

export default Profile;
