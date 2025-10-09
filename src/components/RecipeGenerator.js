import React, { useState } from 'react';
import { Sparkles, Coffee, Clock, Thermometer, Scale, ArrowDown } from 'lucide-react';

const RecipeGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [recipe, setRecipe] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const mockRecipes = {
    'sunny sunday morning': {
      title: 'Bright Sunday Pour Over',
      bean: 'Ethiopian Yirgacheffe',
      method: 'Pour Over (V60)',
      description: 'A light, floral brew perfect for a relaxing Sunday morning. This recipe brings out the citrus and tea-like notes.',
      ingredients: {
        coffee: '20g',
        water: '320g',
        temperature: '200°F (93°C)',
        grindSize: 'Medium-Fine'
      },
      steps: [
        { time: '0:00', action: 'Rinse filter with hot water', icon: '💧' },
        { time: '0:30', action: 'Add 20g ground coffee', icon: '☕' },
        { time: '0:45', action: 'Bloom with 40g water', icon: '🌸' },
        { time: '1:15', action: 'Pour to 160g in circles', icon: '⭕' },
        { time: '2:00', action: 'Pour to 320g total', icon: '💦' },
        { time: '3:30', action: 'Wait for drawdown', icon: '⏱️' },
        { time: '4:00', action: 'Enjoy your coffee!', icon: '😊' }
      ],
      totalTime: '4 minutes',
      yield: '300ml'
    },
    'default': {
      title: 'Classic Morning Brew',
      bean: 'Colombian Supremo',
      method: 'French Press',
      description: 'A rich, full-bodied coffee that highlights chocolate and caramel notes. Perfect for any occasion.',
      ingredients: {
        coffee: '30g',
        water: '500g',
        temperature: '200°F (93°C)',
        grindSize: 'Coarse'
      },
      steps: [
        { time: '0:00', action: 'Boil water to 200°F', icon: '🔥' },
        { time: '0:30', action: 'Add 30g coarse ground coffee', icon: '☕' },
        { time: '1:00', action: 'Pour 500g hot water', icon: '💧' },
        { time: '1:15', action: 'Stir gently', icon: '🥄' },
        { time: '1:30', action: 'Place lid, wait 4 minutes', icon: '⏱️' },
        { time: '5:30', action: 'Press plunger slowly', icon: '👇' },
        { time: '6:00', action: 'Pour and enjoy!', icon: '☕' }
      ],
      totalTime: '6 minutes',
      yield: '480ml'
    }
  };

  const handleGenerate = () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt!');
      return;
    }

    setIsGenerating(true);

    // Simulate API call
    setTimeout(() => {
      const normalizedPrompt = prompt.toLowerCase();
      let selectedRecipe = mockRecipes['default'];

      // Simple keyword matching
      if (normalizedPrompt.includes('sunday') || normalizedPrompt.includes('morning') || normalizedPrompt.includes('sunny')) {
        selectedRecipe = mockRecipes['sunny sunday morning'];
      }

      setRecipe(selectedRecipe);
      setIsGenerating(false);
    }, 1500);
  };

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-coffee-900 flex items-center justify-center">
          <Sparkles className="mr-2 text-coffee-700" />
          Recipe Generator
        </h2>
        <p className="text-coffee-600 text-sm mt-1">Describe your perfect coffee moment</p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-2xl shadow-md p-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Help me design a recipe for a sunny Sunday morning..."
          className="w-full h-24 p-3 border-2 border-coffee-200 rounded-lg focus:outline-none focus:border-coffee-700 resize-none text-coffee-900"
        />
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`w-full mt-3 py-3 rounded-lg font-semibold text-white transition-colors ${
            isGenerating
              ? 'bg-coffee-400 cursor-not-allowed'
              : 'bg-coffee-700 hover:bg-coffee-800'
          }`}
        >
          {isGenerating ? (
            <span className="flex items-center justify-center">
              <span className="animate-spin mr-2">⚙️</span>
              Brewing Recipe...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <Sparkles className="mr-2" size={20} />
              Generate Recipe
            </span>
          )}
        </button>
      </div>

      {/* Recipe Output */}
      {recipe && (
        <div className="space-y-4 animate-fadeIn">
          {/* Recipe Header */}
          <div className="bg-gradient-to-r from-coffee-700 to-coffee-800 rounded-2xl shadow-md p-6 text-white">
            <h3 className="text-2xl font-bold mb-2">{recipe.title}</h3>
            <p className="text-coffee-100 text-sm mb-3">{recipe.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center">
                <Coffee className="mr-1" size={16} />
                {recipe.bean}
              </span>
              <span className="flex items-center">
                <Clock className="mr-1" size={16} />
                {recipe.totalTime}
              </span>
            </div>
          </div>

          {/* Ingredients */}
          <div className="bg-white rounded-2xl shadow-md p-4">
            <h4 className="font-bold text-coffee-900 mb-3 flex items-center">
              <Scale className="mr-2 text-coffee-700" size={18} />
              Ingredients & Setup
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs text-coffee-600 mb-1">Coffee</p>
                <p className="font-bold text-coffee-900">{recipe.ingredients.coffee}</p>
              </div>
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs text-coffee-600 mb-1">Water</p>
                <p className="font-bold text-coffee-900">{recipe.ingredients.water}</p>
              </div>
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs text-coffee-600 mb-1">Temperature</p>
                <p className="font-bold text-coffee-900 text-sm">{recipe.ingredients.temperature}</p>
              </div>
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs text-coffee-600 mb-1">Grind Size</p>
                <p className="font-bold text-coffee-900">{recipe.ingredients.grindSize}</p>
              </div>
            </div>
            <div className="mt-3 bg-coffee-700 text-white rounded-lg p-3 text-center">
              <p className="text-sm font-semibold">Method: {recipe.method}</p>
            </div>
          </div>

          {/* Brew Diagram */}
          <div className="bg-white rounded-2xl shadow-md p-4">
            <h4 className="font-bold text-coffee-900 mb-4 flex items-center">
              <Coffee className="mr-2 text-coffee-700" size={18} />
              Brewing Steps
            </h4>
            <div className="space-y-2">
              {recipe.steps.map((step, index) => (
                <div key={index}>
                  <div className="flex items-start gap-3 bg-coffee-50 rounded-lg p-3 hover:bg-coffee-100 transition-colors">
                    <div className="flex-shrink-0 w-12 h-12 bg-coffee-700 text-white rounded-full flex items-center justify-center text-xl">
                      {step.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-coffee-700">{step.time}</span>
                      </div>
                      <p className="text-sm text-coffee-900 font-medium">{step.action}</p>
                    </div>
                  </div>
                  {index < recipe.steps.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="text-coffee-400" size={20} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Final Note */}
          <div className="bg-gradient-to-r from-amber-100 to-coffee-100 rounded-2xl shadow-md p-4 border-2 border-coffee-300">
            <p className="text-center text-coffee-900 font-semibold">
              ☕ Yields approximately {recipe.yield} of delicious coffee
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!recipe && !isGenerating && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">☕</div>
          <p className="text-coffee-600">Enter a prompt above to generate your perfect recipe</p>
        </div>
      )}
    </div>
  );
};

export default RecipeGenerator;
