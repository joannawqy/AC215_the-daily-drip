import React, { useEffect, useMemo, useState } from 'react';
import {
  Sparkles,
  Coffee,
  Clock,
  Thermometer,
  Scale,
  Droplet,
  Loader2,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  Database,
  Pencil,
} from 'lucide-react';
import { brewRecipe, visualizeRecipe, submitFeedback } from '../services/agentClient';

const brewerOptions = ['V60', 'April', 'Orea', 'Origami'];

const manualTemplate = {
  name: '',
  origin: '',
  process: '',
  variety: '',
  roast_level: '',
  roasted_on: '',
  altitude: '',
  flavor_notes: '',
};

function computeRoastedDays(roastedOn) {
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
  const diffDays = Math.floor((todayUtc - roastUtc) / (1000 * 60 * 60 * 24));
  return diffDays < 0 ? 0 : diffDays;
}

function buildManualPayload(formState) {
  const numericFields = ['roast_level', 'altitude'];
  const base = {
    name: formState.name.trim(),
    origin: formState.origin.trim() || undefined,
    process: formState.process.trim() || undefined,
    variety: formState.variety.trim() || undefined,
  };

  numericFields.forEach((field) => {
    const value = formState[field];
    if (value === '') {
      return;
    }
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      base[field] = parsed;
    }
  });

  const flavorNotes = formState.flavor_notes
    .split(',')
    .map((note) => note.trim())
    .filter(Boolean);
  base.flavor_notes = flavorNotes;

  if (formState.roasted_on) {
    base.roasted_on = formState.roasted_on;
    const computedDays = computeRoastedDays(formState.roasted_on);
    if (computedDays !== null) {
      base.roasted_days = computedDays;
    }
  }

  return base;
}

function stripBeanMetadata(bean) {
  const { bean_id, created_at, updated_at, ...rest } = bean;
  return rest;
}

function formatPourStep(step, index) {
  return (
    <div
      key={`${step.start}-${step.end}-${index}`}
      className="flex items-start gap-3 bg-coffee-50 rounded-lg p-3 border border-coffee-100"
    >
      <div className="flex-shrink-0 w-12 h-12 bg-coffee-700 text-white rounded-full flex items-center justify-center">
        <Droplet size={20} />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-bold text-coffee-700">
            {step.start}s → {step.end}s
          </span>
          <span className="text-xs text-coffee-600">{step.water_added}g</span>
        </div>
        <p className="text-sm text-coffee-900 font-medium">Controlled pour</p>
      </div>
    </div>
  );
}

function RatioBadge({ dose, water }) {
  if (!dose || !water) {
    return null;
  }
  const ratio = (water / dose).toFixed(1);
  return (
    <span className="inline-flex items-center gap-1 bg-coffee-100 text-coffee-900 px-3 py-1 rounded-full text-xs font-semibold">
      <Scale size={14} />
      Ratio 1:{ratio}
    </span>
  );
}

function BeanSummary({ bean }) {
  if (!bean) {
    return null;
  }
  return (
    <div className="grid sm:grid-cols-2 gap-3 text-sm text-coffee-700 mt-3">
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Origin</p>
        <p className="text-coffee-900 font-semibold mt-1">{bean.origin || '—'}</p>
      </div>
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Process</p>
        <p className="text-coffee-900 font-semibold mt-1">{bean.process || '—'}</p>
      </div>
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Variety</p>
        <p className="text-coffee-900 font-semibold mt-1">{bean.variety || '—'}</p>
      </div>
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Roast level</p>
        <p className="text-coffee-900 font-semibold mt-1">
          {bean.roast_level !== undefined && bean.roast_level !== null ? bean.roast_level : '—'}
        </p>
      </div>
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Roasted on</p>
        <p className="text-coffee-900 font-semibold mt-1">
          {bean.roasted_on || '—'}
        </p>
      </div>
      <div className="bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Days since roast</p>
        <p className="text-coffee-900 font-semibold mt-1">
          {bean.roasted_days !== undefined && bean.roasted_days !== null
            ? bean.roasted_days
            : bean.roasted_on
              ? computeRoastedDays(bean.roasted_on) ?? '—'
              : '—'}
        </p>
      </div>
      <div className="sm:col-span-2 bg-coffee-50 rounded-lg p-3 border border-coffee-100">
        <p className="text-xs uppercase text-coffee-500">Flavor notes</p>
        <p className="text-coffee-900 font-semibold mt-1">
          {Array.isArray(bean.flavor_notes) && bean.flavor_notes.length > 0
            ? bean.flavor_notes.join(', ')
            : '—'}
        </p>
      </div>
    </div>
  );
}


function FeedbackForm({ onSubmit, isSubmitting }) {
  const [liking, setLiking] = useState(8);
  const [jag, setJag] = useState({
    flavour_intensity: 3,
    acidity: 3,
    mouthfeel: 3,
    sweetness: 3,
    purchase_intent: 3,
  });

  const handleJagChange = (key, val) => {
    setJag((prev) => ({ ...prev, [key]: val }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      liking,
      jag,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-md p-6 border border-coffee-100 space-y-4">
      <h4 className="font-bold text-coffee-900 flex items-center gap-2">
        <Sparkles size={18} className="text-coffee-700" />
        Rate this Brew
      </h4>

      <div>
        <label className="block text-sm font-semibold text-coffee-700 mb-1">
          Overall Liking (0-10)
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="0"
            max="10"
            value={liking}
            onChange={(e) => setLiking(Number(e.target.value))}
            className="w-full h-2 bg-coffee-200 rounded-lg appearance-none cursor-pointer accent-coffee-700"
          />
          <span className="text-lg font-bold text-coffee-900 w-8 text-center">{liking}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.keys(jag).map((key) => (
          <div key={key}>
            <label className="block text-sm font-semibold text-coffee-700 mb-1 capitalize">
              {key.replace('_', ' ')} (1-5)
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => handleJagChange(key, val)}
                  className={`w-8 h-8 rounded-full text-sm font-bold transition-colors ${jag[key] === val
                    ? 'bg-coffee-700 text-white'
                    : 'bg-coffee-50 text-coffee-700 hover:bg-coffee-100'
                    }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full py-3 rounded-lg font-semibold text-white transition-colors ${isSubmitting ? 'bg-coffee-400 cursor-not-allowed' : 'bg-coffee-700 hover:bg-coffee-800'
          }`}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
      </button>
    </form>
  );
}

const RecipeGenerator = ({ beans, onRefreshBeans }) => {
  const [mode, setMode] = useState(beans.length > 0 ? 'library' : 'manual');
  const [selectedBeanId, setSelectedBeanId] = useState(beans[0]?.bean_id || '');
  const [manualForm, setManualForm] = useState(manualTemplate);
  const [brewer, setBrewer] = useState('V60');
  const [note, setNote] = useState('');
  const [ragEnabled, setRagEnabled] = useState(true);
  const [ragK, setRagK] = useState(3);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [session, setSession] = useState(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  useEffect(() => {
    if (mode === 'library' && beans.length === 0) {
      setMode('manual');
    }
    if (mode === 'library' && beans.length > 0 && !beans.find((bean) => bean.bean_id === selectedBeanId)) {
      setSelectedBeanId(beans[0].bean_id);
    }
  }, [beans, mode, selectedBeanId]);

  const ragKValue = useMemo(() => {
    const parsed = Number(ragK);
    if (Number.isNaN(parsed) || parsed < 1) {
      return 1;
    }
    if (parsed > 10) {
      return 10;
    }
    return Math.floor(parsed);
  }, [ragK]);

  const handleManualChange = (field) => (event) => {
    const value = event.target.value;
    setManualForm((prev) => ({ ...prev, [field]: value }));
  };

  const activeLibraryBean = useMemo(
    () => beans.find((bean) => bean.bean_id === selectedBeanId),
    [beans, selectedBeanId],
  );

  const beanPayload = () => {
    if (mode === 'library') {
      if (!activeLibraryBean) {
        setError('Select a bean from your library.');
        return null;
      }
      const payload = { ...stripBeanMetadata(activeLibraryBean) };
      if (!Array.isArray(payload.flavor_notes)) {
        payload.flavor_notes = payload.flavor_notes ? [payload.flavor_notes] : [];
      }
      if (payload.roasted_on) {
        const computed = computeRoastedDays(payload.roasted_on);
        if (computed !== null) {
          payload.roasted_days = computed;
        }
      }
      return payload;
    }
    const manualBean = buildManualPayload(manualForm);
    if (!manualBean.name) {
      setError('Bean name is required for manual entry.');
      return null;
    }
    if (!Array.isArray(manualBean.flavor_notes)) {
      manualBean.flavor_notes = [];
    }
    if (manualBean.roasted_on && (manualBean.roasted_days === undefined || manualBean.roasted_days === null)) {
      const computed = computeRoastedDays(manualBean.roasted_on);
      if (computed !== null) {
        manualBean.roasted_days = computed;
      }
    }
    return manualBean;
  };

  const handleGenerate = async (event) => {
    event.preventDefault();
    setError(null);
    setFeedbackSubmitted(false);

    const bean = beanPayload();
    if (!bean) {
      return;
    }
    if (!brewer) {
      setError('Brewer selection is required.');
      return;
    }

    setIsGenerating(true);

    try {
      const payload = {
        bean,
        brewer,
        rag_enabled: ragEnabled,
        rag_k: ragKValue,
      };
      if (note.trim()) {
        payload.note = note.trim();
      }
      const brewResult = await brewRecipe(payload);
      const completeRecipe = {
        bean,
        ...brewResult.recipe,
      };
      const visualizationResult = await visualizeRecipe(completeRecipe, ['html', 'ascii']);
      setSession({
        bean,
        brewer,
        note: note.trim(),
        references: brewResult.references,
        recipe: brewResult.recipe,
        visualization: visualizationResult,
        beanSource: mode === 'library' ? activeLibraryBean?.name : 'Manual entry',
      });
      if (typeof onRefreshBeans === 'function') {
        onRefreshBeans();
      }
    } catch (apiError) {
      setSession(null);
      setError(apiError.message || 'Failed to generate recipe.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFeedbackSubmit = async (evaluation) => {
    if (!session) return;
    setIsSubmittingFeedback(true);
    try {
      await submitFeedback({
        bean: session.bean,
        recipe: session.recipe,
        evaluation,
      });
      setFeedbackSubmitted(true);
    } catch (err) {
      setError(err.message || 'Failed to submit feedback');
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const pours = session?.recipe?.brewing?.pours || [];
  const summary = session?.visualization?.summary;
  const htmlVisualization = session?.visualization?.outputs?.html;
  const asciiVisualization = session?.visualization?.outputs?.ascii;

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-2xl shadow-sm border border-coffee-100 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-coffee-900 flex items-center gap-2">
              <Sparkles className="text-coffee-700" />
              Recipe Studio
            </h2>
            <p className="text-sm text-coffee-600">
              Use a saved bean or describe one manually, then let the agent craft the pour schedule.
            </p>
          </div>
          <div className="inline-flex bg-coffee-50 border border-coffee-200 rounded-full overflow-hidden">
            <button
              type="button"
              onClick={() => setMode('library')}
              disabled={beans.length === 0}
              className={`px-4 py-2 text-sm font-semibold transition-colors flex items-center gap-2 ${mode === 'library' ? 'bg-coffee-700 text-white' : 'text-coffee-700'
                } ${beans.length === 0 ? 'cursor-not-allowed opacity-50' : ''}`}
            >
              <Database size={16} />
              Saved bean
            </button>
            <button
              type="button"
              onClick={() => setMode('manual')}
              className={`px-4 py-2 text-sm font-semibold transition-colors flex items-center gap-2 ${mode === 'manual' ? 'bg-coffee-700 text-white' : 'text-coffee-700'
                }`}
            >
              <Pencil size={16} />
              Manual entry
            </button>
          </div>
        </div>

        <form onSubmit={handleGenerate} className="space-y-5">
          {mode === 'library' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Choose a bean
                </label>
                <select
                  value={selectedBeanId}
                  onChange={(event) => setSelectedBeanId(event.target.value)}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                >
                  {beans.map((bean) => (
                    <option key={bean.bean_id} value={bean.bean_id}>
                      {bean.name} {bean.origin ? `• ${bean.origin}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <BeanSummary bean={activeLibraryBean} />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Bean name *
                </label>
                <input
                  type="text"
                  required
                  value={manualForm.name}
                  onChange={handleManualChange('name')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Origin</label>
                <input
                  type="text"
                  value={manualForm.origin}
                  onChange={handleManualChange('origin')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Process</label>
                <input
                  type="text"
                  value={manualForm.process}
                  onChange={handleManualChange('process')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">Variety</label>
                <input
                  type="text"
                  value={manualForm.variety}
                  onChange={handleManualChange('variety')}
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
                  value={manualForm.roast_level}
                  onChange={handleManualChange('roast_level')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Roasted on
                </label>
                <input
                  type="date"
                  value={manualForm.roasted_on}
                  onChange={handleManualChange('roasted_on')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
                <p className="text-xs text-coffee-500 mt-1">
                  The app will calculate days since roast automatically.
                </p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Altitude (masl)
                </label>
                <input
                  type="number"
                  min="0"
                  value={manualForm.altitude}
                  onChange={handleManualChange('altitude')}
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold text-coffee-700 mb-1">
                  Flavor notes
                </label>
                <textarea
                  value={manualForm.flavor_notes}
                  onChange={handleManualChange('flavor_notes')}
                  rows={2}
                  placeholder="floral, citrus, cacao"
                  className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900 resize-y"
                />
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-coffee-700 mb-1">Brewer *</label>
              <select
                value={brewer}
                onChange={(event) => setBrewer(event.target.value)}
                className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
              >
                {brewerOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-coffee-700 mb-1">
                Custom note
              </label>
              <input
                type="text"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="e.g., sweeter cup, shorter brew"
                className="w-full border-2 border-coffee-200 rounded-lg px-3 py-2 focus:outline-none focus:border-coffee-700 text-coffee-900"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 border border-coffee-100 rounded-xl p-4 bg-coffee-50">
            <div className="flex items-center gap-2">
              <input
                id="rag-enabled"
                type="checkbox"
                checked={ragEnabled}
                onChange={(event) => setRagEnabled(event.target.checked)}
                className="h-4 w-4 accent-coffee-700"
              />
              <label htmlFor="rag-enabled" className="text-sm text-coffee-800">
                Retrieve reference brews (RAG)
              </label>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="rag-k" className="text-sm text-coffee-700">
                Max references
              </label>
              <input
                id="rag-k"
                type="number"
                min="1"
                max="10"
                value={ragK}
                onChange={(event) => setRagK(event.target.value)}
                className="w-20 p-2 border border-coffee-200 rounded-lg focus:outline-none focus:border-coffee-700 text-coffee-900"
              />
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isGenerating}
            className={`w-full py-3 rounded-lg font-semibold text-white transition-colors flex items-center justify-center gap-2 ${isGenerating ? 'bg-coffee-400 cursor-not-allowed' : 'bg-coffee-700 hover:bg-coffee-800'
              }`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Brewing with the agent...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Generate recipe
              </>
            )}
          </button>
        </form>
      </section>

      {session && (
        <section className="space-y-6 animate-fadeIn">
          <div className="bg-gradient-to-r from-coffee-700 to-coffee-800 rounded-2xl shadow-md p-6 text-white">
            <div className="flex items-center gap-2 text-sm uppercase tracking-wide text-coffee-200 mb-2">
              <CheckCircle2 size={16} />
              Agent response ready
            </div>
            <h3 className="text-2xl font-bold mb-2">{session.bean.name}</h3>
            <p className="text-coffee-100 text-sm mb-4">
              {session.note ? `Preference: ${session.note}` : 'Balanced pour-over plan tailored to your bean.'}
            </p>
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="flex items-center gap-1">
                <Coffee size={16} />
                {session.recipe?.brewing?.dose || '--'} g coffee
              </span>
              <span className="flex items-center gap-1">
                <Droplet size={16} />
                {session.recipe?.brewing?.target_water || '--'} g water
              </span>
              <span className="flex items-center gap-1">
                <Thermometer size={16} />
                {session.recipe?.brewing?.temperature || '--'} °C
              </span>
              <span className="flex items-center gap-1">
                <Clock size={16} />
                {summary?.total_time ? `${summary.total_time}s` : '--'}
              </span>
              <RatioBadge
                dose={session.recipe?.brewing?.dose}
                water={session.recipe?.brewing?.target_water}
              />
            </div>
            <p className="text-xs text-coffee-100 mt-3">Source: {session.beanSource}</p>
          </div>

          <div className="bg-white rounded-2xl shadow-md p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-coffee-900 flex items-center gap-2">
                <Scale size={18} className="text-coffee-700" />
                Brewing profile
              </h4>
              <span className="text-xs font-semibold text-coffee-500 bg-coffee-100 px-2 py-1 rounded">
                {session.brewer}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm text-coffee-700">
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs uppercase tracking-wide text-coffee-500">Grind size</p>
                <p className="text-base font-semibold text-coffee-900">
                  {session.recipe?.brewing?.grinding_size || '--'}
                </p>
              </div>
              <div className="bg-coffee-50 rounded-lg p-3">
                <p className="text-xs uppercase tracking-wide text-coffee-500">Total pours</p>
                <p className="text-base font-semibold text-coffee-900">{pours.length}</p>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="text-sm font-semibold text-coffee-800 flex items-center gap-2">
                <Droplet size={16} className="text-coffee-700" />
                Pour schedule
              </h5>
              <div className="space-y-2">
                {pours.map((step, index) => formatPourStep(step, index))}
              </div>
            </div>
          </div>

          {session.references?.length > 0 && (
            <div className="bg-white rounded-2xl shadow-md p-4 space-y-3 border border-coffee-100">
              <h4 className="font-semibold text-coffee-900 flex items-center gap-2">
                <BookOpen size={18} className="text-coffee-700" />
                Reference brews
              </h4>
              <div className="space-y-3">
                {session.references.map((ref) => (
                  <div
                    key={ref.id}
                    className="border border-coffee-100 rounded-xl p-3 bg-coffee-50"
                  >
                    <div className="flex items-center justify-between text-xs text-coffee-600 mb-1">
                      <span>Match #{ref.rank}</span>
                      <span>Distance: {ref.distance.toFixed(3)}</span>
                    </div>
                    <p className="text-sm text-coffee-800 mb-2">{ref.bean_text}</p>
                    {ref.brewing && (
                      <div className="grid grid-cols-2 gap-2 text-xs text-coffee-700">
                        <span>Brewer: {ref.brewing.brewer || 'N/A'}</span>
                        <span>Temperature: {ref.brewing.temperature || '—'}°C</span>
                        <span>Dose: {ref.brewing.dose || '—'}g</span>
                        <span>Water: {ref.brewing.target_water || '—'}g</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {htmlVisualization && (
            <div className="bg-white rounded-2xl shadow-md p-4">
              <h4 className="font-semibold text-coffee-900 mb-3 flex items-center gap-2">
                <Sparkles size={18} className="text-coffee-700" />
                Timeline visualization
              </h4>
              <div
                className="border border-coffee-100 rounded-xl overflow-hidden"
                dangerouslySetInnerHTML={{ __html: htmlVisualization }}
              />
            </div>
          )}

          {asciiVisualization && (
            <div className="bg-coffee-900 text-coffee-50 rounded-2xl shadow-md p-4">
              <h4 className="font-semibold text-coffee-100 mb-3 flex items-center gap-2">
                <Clock size={18} />
                ASCII flow
              </h4>
              <pre className="text-xs overflow-x-auto whitespace-pre-wrap">{asciiVisualization}</pre>
            </div>
          )}

          {!feedbackSubmitted ? (
            <FeedbackForm onSubmit={handleFeedbackSubmit} isSubmitting={isSubmittingFeedback} />
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3 text-green-800">
              <CheckCircle2 size={20} />
              <p className="font-medium">Feedback submitted! This brew has been added to the RAG database.</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
};

export {
  computeRoastedDays,
  buildManualPayload,
  stripBeanMetadata,
  formatPourStep,
  RatioBadge,
  BeanSummary,
};

export default RecipeGenerator;
