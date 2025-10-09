import React, { useState } from 'react';
import { Plus, Edit2, Trash2, MapPin, Calendar } from 'lucide-react';

const BeanCollection = () => {
  const [beans, setBeans] = useState([
    {
      id: 1,
      name: 'Ethiopian Yirgacheffe',
      origin: 'Ethiopia',
      roastLevel: 'Light',
      flavorNotes: ['Floral', 'Citrus', 'Tea-like'],
      purchaseDate: '2025-09-15',
      amount: '250g',
      favorite: true
    },
    {
      id: 2,
      name: 'Colombian Supremo',
      origin: 'Colombia',
      roastLevel: 'Medium',
      flavorNotes: ['Chocolate', 'Caramel', 'Nutty'],
      purchaseDate: '2025-09-20',
      amount: '500g',
      favorite: false
    },
    {
      id: 3,
      name: 'Sumatra Mandheling',
      origin: 'Indonesia',
      roastLevel: 'Dark',
      flavorNotes: ['Earthy', 'Herbal', 'Spicy'],
      purchaseDate: '2025-09-10',
      amount: '200g',
      favorite: false
    },
    {
      id: 4,
      name: 'Kenya AA',
      origin: 'Kenya',
      roastLevel: 'Medium-Light',
      flavorNotes: ['Berry', 'Wine', 'Bright'],
      purchaseDate: '2025-09-25',
      amount: '300g',
      favorite: false
    },
    {
      id: 5,
      name: 'Brazil Santos',
      origin: 'Brazil',
      roastLevel: 'Medium-Dark',
      flavorNotes: ['Chocolate', 'Nutty', 'Sweet'],
      purchaseDate: '2025-09-18',
      amount: '400g',
      favorite: false
    }
  ]);

  const [showAddModal, setShowAddModal] = useState(false);

  const handleEdit = (beanId) => {
    alert(`Edit bean ${beanId} (mock interaction)`);
  };

  const handleDelete = (beanId) => {
    if (window.confirm('Delete this bean from your collection?')) {
      setBeans(beans.filter(bean => bean.id !== beanId));
    }
  };

  const handleAdd = () => {
    setShowAddModal(true);
  };

  const getRoastColor = (roastLevel) => {
    const colors = {
      'Light': 'bg-amber-200 text-amber-900',
      'Medium-Light': 'bg-amber-300 text-amber-900',
      'Medium': 'bg-amber-600 text-white',
      'Medium-Dark': 'bg-amber-800 text-white',
      'Dark': 'bg-coffee-900 text-white'
    };
    return colors[roastLevel] || 'bg-gray-400 text-white';
  };

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-coffee-900">My Bean Collection</h2>
        <button
          onClick={handleAdd}
          className="bg-coffee-700 text-white p-2 rounded-full shadow-lg hover:bg-coffee-800 transition-colors"
        >
          <Plus size={24} />
        </button>
      </div>

      {/* Bean Cards */}
      <div className="space-y-3">
        {beans.map((bean) => (
          <div
            key={bean.id}
            className="bg-white rounded-xl shadow-md p-4 hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-coffee-900">{bean.name}</h3>
                  {bean.favorite && <span className="text-yellow-500">⭐</span>}
                </div>
                <div className="flex items-center text-sm text-coffee-600 mt-1">
                  <MapPin size={14} className="mr-1" />
                  {bean.origin}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(bean.id)}
                  className="text-coffee-600 hover:text-coffee-900 p-1"
                >
                  <Edit2 size={18} />
                </button>
                <button
                  onClick={() => handleDelete(bean.id)}
                  className="text-red-500 hover:text-red-700 p-1"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            {/* Roast Level */}
            <div className="mb-3">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getRoastColor(bean.roastLevel)}`}>
                {bean.roastLevel} Roast
              </span>
            </div>

            {/* Flavor Notes */}
            <div className="mb-3">
              <p className="text-xs text-coffee-600 mb-1 font-semibold">Flavor Notes:</p>
              <div className="flex flex-wrap gap-1">
                {bean.flavorNotes.map((note, index) => (
                  <span
                    key={index}
                    className="bg-coffee-50 text-coffee-800 px-2 py-1 rounded text-xs border border-coffee-200"
                  >
                    {note}
                  </span>
                ))}
              </div>
            </div>

            {/* Info Row */}
            <div className="flex justify-between items-center text-xs text-coffee-600 pt-3 border-t border-coffee-100">
              <div className="flex items-center">
                <Calendar size={12} className="mr-1" />
                {bean.purchaseDate}
              </div>
              <div className="font-semibold text-coffee-800">{bean.amount}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Modal (Simple) */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full">
            <h3 className="text-xl font-bold text-coffee-900 mb-4">Add New Bean</h3>
            <p className="text-coffee-600 mb-4">This is a mock interaction. In a real app, you'd have a form here.</p>
            <button
              onClick={() => setShowAddModal(false)}
              className="w-full bg-coffee-700 text-white py-3 rounded-lg font-semibold hover:bg-coffee-800 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BeanCollection;
