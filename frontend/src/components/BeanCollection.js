import React, { useEffect, useMemo, useState } from 'react';
import { Coffee, Edit2, Plus, Trash2 } from 'lucide-react';

const EMPTY_BEAN = {
  name: '',
  origin: '',
  process: '',
  variety: '',
  roast_level: '',
  roasted_on: '',
  altitude: '',
  flavor_notes: '',
};

const computeRoastedDays = (roastedOn) => {
  if (!roastedOn) {
    return null;
  }
  const roastDate = new Date(roastedOn);
  if (Number.isNaN(roastDate.getTime())) {
    return null;
  }
  const today = new Date();
  const todayUtc = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const roastUtc = Date.UTC(roastDate.getFullYear(), roastDate.getMonth(), roastDate.getDate());
  const diff = Math.floor((todayUtc - roastUtc) / (1000 * 60 * 60 * 24));
  return diff < 0 ? 0 : diff;
};

function toPayload(formState) {
  const parseNumber = (value) => {
    if (value === '' || value === null || value === undefined) {
      return null;
    }
    const numeric = Number(value);
    return Number.isNaN(numeric) ? null : numeric;
  };

  return {
    name: formState.name.trim(),
    origin: formState.origin.trim() || null,
    process: formState.process.trim() || null,
    variety: formState.variety.trim() || null,
    roast_level: parseNumber(formState.roast_level),
    roasted_on: formState.roasted_on || null,
    roasted_days: computeRoastedDays(formState.roasted_on) ?? null,
    altitude: parseNumber(formState.altitude),
    flavor_notes: formState.flavor_notes
      .split(',')
      .map((note) => note.trim())
      .filter(Boolean),
  };
}

function fromRecord(record) {
  return {
    name: record.name || '',
    origin: record.origin || '',
    process: record.process || '',
    variety: record.variety || '',
    roast_level: record.roast_level ?? '',
    roasted_on: record.roasted_on || '',
    altitude: record.altitude ?? '',
    flavor_notes: Array.isArray(record.flavor_notes) ? record.flavor_notes.join(', ') : '',
  };
}

function BeanCollection({ beans, loading, onCreate, onUpdate, onDelete }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeBeanId, setActiveBeanId] = useState(null);
  const [form, setForm] = useState(EMPTY_BEAN);
  const [submitting, setSubmitting] = useState(false);
  const isEditing = Boolean(activeBeanId);

  useEffect(() => {
    if (!isModalOpen) {
      setForm(EMPTY_BEAN);
      setActiveBeanId(null);
    }
  }, [isModalOpen]);

  const sortedBeans = useMemo(
    () =>
      [...beans].sort((a, b) => a.name.localeCompare(b.name)),
    [beans],
  );

  const openCreateModal = () => {
    setForm(EMPTY_BEAN);
    setActiveBeanId(null);
    setIsModalOpen(true);
  };

  const openEditModal = (bean) => {
    setActiveBeanId(bean.bean_id);
    setForm(fromRecord(bean));
    setIsModalOpen(true);
  };

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!form.name.trim()) {
      return;
    }
    setSubmitting(true);
    try {
      const payload = toPayload(form);
      if (isEditing) {
        await onUpdate(activeBeanId, payload);
      } else {
        await onCreate(payload);
      }
      setIsModalOpen(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (beanId) => {
    const confirmDelete = window.confirm('Delete this bean from your library?');
    if (!confirmDelete) {
      return;
    }
    await onDelete(beanId);
  };

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-2xl shadow-sm border border-coffee-100 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <div>
            <h2 className="text-2xl font-bold text-coffee-900 flex items-center gap-2">
              <Coffee size={24} className="text-coffee-700" />
              Bean Library
            </h2>
            <p className="text-sm text-coffee-600">
              Store beans once, reuse them when generating recipes.
            </p>
          </div>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-coffee-700 text-white font-semibold hover:bg-coffee-800 transition-colors"
          >
            <Plus size={18} />
            Add bean
          </button>
        </div>

        {loading ? (
          <div className="bg-coffee-50 border border-coffee-100 rounded-xl p-6 text-center text-coffee-600">
            Loading beans…
          </div>
        ) : sortedBeans.length === 0 ? (
          <div className="bg-coffee-50 border border-dashed border-coffee-200 rounded-xl p-6 text-center text-coffee-600">
            Your library is empty. Add beans you love to reuse them across brews.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-coffee-100">
              <thead className="bg-coffee-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Name
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Origin
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Process
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Roast level
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Roasted on
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Flavor notes
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-coffee-600 uppercase tracking-wide">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-coffee-100">
                {sortedBeans.map((bean) => (
                  <tr key={bean.bean_id} className="hover:bg-coffee-50">
                    <td className="px-4 py-3 text-sm text-coffee-900 font-semibold">{bean.name}</td>
                    <td className="px-4 py-3 text-sm text-coffee-700">{bean.origin || '—'}</td>
                    <td className="px-4 py-3 text-sm text-coffee-700">{bean.process || '—'}</td>
                    <td className="px-4 py-3 text-sm text-coffee-700">
                      {bean.roast_level !== null && bean.roast_level !== undefined
                        ? bean.roast_level
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-coffee-700">
                      {bean.roasted_on ? (
                        <div className="flex flex-col">
                          <span>{bean.roasted_on}</span>
                          <span className="text-xs text-coffee-500">
                            {(() => {
                              const days =
                                bean.roasted_days ?? computeRoastedDays(bean.roasted_on);
                              return days !== null && days !== undefined ? `${days} day(s)` : '—';
                            })()}
                          </span>
                        </div>
                      ) : bean.roasted_days !== null && bean.roasted_days !== undefined ? (
                        <span className="text-xs text-coffee-600">
                          {bean.roasted_days} day(s)
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-coffee-700">
                      {Array.isArray(bean.flavor_notes) && bean.flavor_notes.length > 0
                        ? bean.flavor_notes.join(', ')
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          onClick={() => openEditModal(bean)}
                          className="text-coffee-600 hover:text-coffee-900 transition-colors"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(bean.bean_id)}
                          className="text-red-500 hover:text-red-700 transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center px-4 py-6 z-40">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-coffee-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-coffee-900">
                {isEditing ? 'Edit bean' : 'Add new bean'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-coffee-500 hover:text-coffee-900"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Bean name *
                </label>
                <input
                  type="text"
                  required
                  value={form.name}
                  onChange={handleChange('name')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Origin</label>
                <input
                  type="text"
                  value={form.origin}
                  onChange={handleChange('origin')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Process</label>
                <input
                  type="text"
                  value={form.process}
                  onChange={handleChange('process')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Variety</label>
                <input
                  type="text"
                  value={form.variety}
                  onChange={handleChange('variety')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Roast level (0-5)
                </label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={form.roast_level}
                  onChange={handleChange('roast_level')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Roasted on
                </label>
                <input
                  type="date"
                  value={form.roasted_on}
                  onChange={handleChange('roasted_on')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
                <p className="text-xs text-coffee-500 mt-1">
                  We will calculate days since roast whenever you brew.
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Altitude (masl)
                </label>
                <input
                  type="number"
                  min="0"
                  value={form.altitude}
                  onChange={handleChange('altitude')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Flavor notes
                </label>
                <textarea
                  value={form.flavor_notes}
                  onChange={handleChange('flavor_notes')}
                  rows={2}
                  placeholder="floral, citrus, berry"
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900 resize-y"
                />
                <p className="text-xs text-coffee-500 mt-1">
                  Separate notes with commas. Notes are surfaced to the agent and stored in your
                  library.
                </p>
              </div>

              <div className="md:col-span-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-coffee-200 text-coffee-700 hover:bg-coffee-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-5 py-2 rounded-lg font-semibold text-white transition-colors ${
                    submitting ? 'bg-coffee-400 cursor-not-allowed' : 'bg-coffee-700 hover:bg-coffee-800'
                  }`}
                >
                  {submitting ? 'Saving…' : isEditing ? 'Update bean' : 'Save bean'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default BeanCollection;
