import React, { useState } from 'react';
import { X, Shield, Plus, Loader2 } from 'lucide-react';
import { squadsApi } from '../../api/squadsApi';

const GAME_OPTIONS = [
  'VALORANT',
  'Apex Legends',
  'CS2',
  'Rainbow Six Siege',
  'Call of Duty',
];

export default function CreateSquadModal({ isOpen, onClose, onSquadCreated }) {
  const [name, setName] = useState('');
  const [game, setGame] = useState('VALORANT');
  const [description, setDescription] = useState('');
  const [synergy, setSynergy] = useState(88);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg('Squad name is required.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    try {
      const payload = {
        name: name.trim(),
        game,
        description: description.trim() || undefined,
        synergy_score: Number(synergy) || 85.0,
      };

      const res = await squadsApi.createSquad(payload);
      const createdTeam = res.data?.data || res.data;
      if (onSquadCreated) onSquadCreated(createdTeam);
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create squad.';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modalOverlay" onClick={onClose}>
      <div
        className="modalContainer glassCard"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '500px' }}
      >
        <button
          type="button"
          className="modalCloseBtn"
          onClick={onClose}
        >
          <X size={20} />
        </button>

        <div style={{ textAlign: 'left', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Shield size={20} color="var(--cyan)" />
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>Create Competitive Squad</h2>
          </div>
          <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0 }}>
            Establish a persistent roster with role assignments and synergy tracking.
          </p>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#f87171',
            padding: '10px 14px',
            borderRadius: 'var(--radius-buttons)',
            fontSize: '12px',
            marginBottom: '16px',
            textAlign: 'left'
          }}>
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ textAlign: 'left' }}>
          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="squadName" style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              SQUAD NAME
            </label>
            <input
              id="squadName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Phantom Vanguard"
              required
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-buttons)',
                padding: '10px 14px',
                color: '#ffffff',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="squadGame" style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              TARGET COMPETITIVE TITLE
            </label>
            <select
              id="squadGame"
              value={game}
              onChange={(e) => setGame(e.target.value)}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-buttons)',
                padding: '10px 14px',
                color: '#ffffff',
                fontSize: '13px',
                outline: 'none'
              }}
            >
              {GAME_OPTIONS.map((g) => (
                <option key={g} value={g} style={{ background: '#0d1321', color: '#ffffff' }}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="squadDesc" style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              SQUAD MISSION & PLAYSTYLE (OPTIONAL)
            </label>
            <textarea
              id="squadDesc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your schedule, competitive goals, and team playstyle..."
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-buttons)',
                padding: '10px 14px',
                color: '#ffffff',
                fontSize: '13px',
                outline: 'none',
                resize: 'vertical'
              }}
            />
          </div>

          <div style={{ marginBottom: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label htmlFor="squadSynergy" style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
                INITIAL TARGET SYNERGY
              </label>
              <span style={{ fontSize: '12px', fontFamily: 'var(--font-geistmono)', color: 'var(--cyan)', fontWeight: 600 }}>
                {synergy}%
              </span>
            </div>
            <input
              id="squadSynergy"
              type="range"
              min="50"
              max="99"
              value={synergy}
              onChange={(e) => setSynergy(e.target.value)}
              style={{ width: '100%', accentColor: 'var(--cyan)' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button type="button" className="glassBtn" onClick={onClose} disabled={loading} style={{ padding: '8px 16px', fontSize: '13px' }}>
              Cancel
            </button>
            <button type="submit" className="primaryBtn" disabled={loading} style={{ padding: '8px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
              <span>{loading ? 'Creating Squad...' : 'Create Squad'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
