import React, { useState } from 'react';
import { newsApi } from '../../api/newsApi';
import { X, Send, Newspaper, AlertCircle } from 'lucide-react';

const SUPPORTED_GAMES = [
  'General',
  'VALORANT',
  'CS2',
  'Apex Legends',
  'Dota 2',
  'Rainbow Six Siege',
  'Call of Duty'
];

const CATEGORIES = [
  'Esports',
  'Patch Notes',
  'Announcements',
  'Community'
];

function CreateArticleModal({ isOpen, onClose, onArticleCreated }) {
  const [formData, setFormData] = useState({
    title: '',
    summary: '',
    content: '',
    game: 'General',
    category: 'Esports',
    source_url: '',
    image_url: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.summary.trim()) {
      setError('Title and Summary are required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        title: formData.title.trim(),
        summary: formData.summary.trim(),
        content: formData.content.trim() || null,
        game: formData.game,
        category: formData.category,
        source_url: formData.source_url.trim() || null,
        image_url: formData.image_url.trim() || null
      };

      const res = await newsApi.createArticle(payload);
      const article = res?.data || res;
      if (article && onArticleCreated) {
        onArticleCreated(article);
      }
      onClose();
    } catch (err) {
      console.error('Failed to create article:', err);
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to publish article.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modalOverlay" onClick={onClose} style={{ zIndex: 1000 }}>
      <div 
        className="modalContainer glassCard"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '620px',
          maxHeight: '90vh',
          overflowY: 'auto',
          textAlign: 'left'
        }}
      >
        <button 
          type="button" 
          className="modalCloseBtn"
          onClick={onClose}
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <Newspaper color="var(--cyan)" size={22} />
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#ffffff', fontFamily: "'Space Grotesk', sans-serif" }}>
            Publish Gaming News / Patch Note
          </h3>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            marginBottom: '16px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.35)',
            borderRadius: 'var(--radius-buttons)',
            color: '#f87171',
            fontSize: '12px'
          }}>
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="formGroup" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              ARTICLE HEADLINE / TITLE *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="e.g. VALORANT Patch 9.04 Competitive Agent Balancing"
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
            <div className="formGroup">
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                GAME TITLE
              </label>
              <select
                name="game"
                value={formData.game}
                onChange={handleChange}
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
                {SUPPORTED_GAMES.map(g => (
                  <option key={g} value={g} style={{ background: '#0d1321', color: '#ffffff' }}>{g}</option>
                ))}
              </select>
            </div>

            <div className="formGroup">
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                CATEGORY
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
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
                {CATEGORIES.map(c => (
                  <option key={c} value={c} style={{ background: '#0d1321', color: '#ffffff' }}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="formGroup" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              SUMMARY / KEY HIGHLIGHTS *
            </label>
            <textarea
              name="summary"
              value={formData.summary}
              onChange={handleChange}
              rows={3}
              placeholder="Concise overview of changes or tournament meta developments..."
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
                outline: 'none',
                resize: 'vertical'
              }}
            />
          </div>

          <div className="formGroup" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
              FULL CONTENT / PATCH DETAILS
            </label>
            <textarea
              name="content"
              value={formData.content}
              onChange={handleChange}
              rows={5}
              placeholder="Full article body, patch notes breakdown, stats updates..."
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '22px' }}>
            <div className="formGroup">
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                EXTERNAL SOURCE URL
              </label>
              <input
                type="url"
                name="source_url"
                value={formData.source_url}
                onChange={handleChange}
                placeholder="https://playvalorant.com/..."
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

            <div className="formGroup">
              <label style={{ display: 'block', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)', marginBottom: '6px' }}>
                COVER IMAGE URL (OPTIONAL)
              </label>
              <input
                type="url"
                name="image_url"
                value={formData.image_url}
                onChange={handleChange}
                placeholder="https://images.unsplash.com/..."
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
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              className="glassBtn"
              style={{ padding: '8px 16px', fontSize: '13px' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="primaryBtn"
              style={{ padding: '8px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Send size={13} />
              <span>{isSubmitting ? 'Publishing...' : 'Publish Article'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateArticleModal;
