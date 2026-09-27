import React, { useState, useEffect, useCallback } from 'react';
import { newsApi } from '../../api/newsApi';
import { useAuth } from '../../context/AuthContext';
import CreateArticleModal from './CreateArticleModal';
import { 
  Newspaper, 
  FileText, 
  ExternalLink, 
  Plus, 
  Calendar, 
  Gamepad2,
  X
} from 'lucide-react';

const CATEGORIES = ['All', 'Esports', 'Patch Notes', 'Announcements'];
const GAMES = ['All', 'VALORANT', 'CS2', 'Apex Legends', 'Dota 2', 'Rainbow Six Siege', 'Call of Duty'];

function getCategoryColor(category) {
  switch (category?.toLowerCase()) {
    case 'esports':
      return { bg: 'rgba(234, 179, 8, 0.15)', color: '#facc15', border: 'rgba(234, 179, 8, 0.35)' };
    case 'patch notes':
      return { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.35)' };
    case 'announcements':
      return { bg: 'rgba(244, 63, 94, 0.15)', color: '#f43f5e', border: 'rgba(244, 63, 94, 0.35)' };
    default:
      return { bg: 'rgba(34, 211, 238, 0.15)', color: '#22d3ee', border: 'rgba(34, 211, 238, 0.35)' };
  }
}

function NewsHub() {
  const { isAdmin } = useAuth();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedGame, setSelectedGame] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [activeArticleModal, setActiveArticleModal] = useState(null);

  const fetchNews = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await newsApi.getNews(
        selectedGame === 'All' ? null : selectedGame,
        selectedCategory === 'All' ? null : selectedCategory,
        30
      );
      const articleList = res?.data?.data || res?.data || (Array.isArray(res) ? res : []);
      setArticles(articleList);
    } catch (err) {
      console.error('Failed to fetch news feed:', err);
      setError('Could not load esports news feed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [selectedGame, selectedCategory]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const handleArticleCreated = (newArticle) => {
    setArticles(prev => [newArticle, ...prev]);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recent';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'left' }}>
      {/* HEADER SECTION */}
      <div className="glassCard" style={{
        padding: '28px',
        marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <Newspaper size={24} color="var(--cyan)" />
              <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
                Esports Hub & Patch Notes
              </h1>
              <span className="matchBadge">
                LIVE TELEMETRY
              </span>
            </div>
            <p style={{ color: 'var(--text2)', margin: 0, fontSize: '13px', maxWidth: '650px' }}>
              Stay ahead of competitive balance updates, meta shifts, and tournament schedules across major competitive titles.
            </p>
          </div>

          {isAdmin && (
            <button
              type="button"
              className="primaryBtn"
              onClick={() => setIsCreateModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 18px',
                fontSize: '13px'
              }}
            >
              <Plus size={15} />
              <span>Publish Update</span>
            </button>
          )}
        </div>

        {/* FILTER BAR */}
        <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '14px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
          {/* CATEGORIES */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', marginRight: '4px', fontWeight: 600 }}>
              CATEGORY:
            </span>
            {CATEGORIES.map(cat => {
              const isSelected = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    padding: '4px 14px',
                    borderRadius: 'var(--radius-pills)',
                    fontSize: '12px',
                    fontWeight: isSelected ? 600 : 500,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                    background: isSelected ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    color: isSelected ? '#ffffff' : 'var(--text2)',
                    boxShadow: isSelected ? '0 0 12px rgba(34, 211, 238, 0.25)' : 'none',
                    fontFamily: "'Space Grotesk', sans-serif"
                  }}
                >
                  {cat}
                </button>
              );
            })}
          </div>

          {/* GAMES */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', marginRight: '4px', fontWeight: 600 }}>
              GAME TITLE:
            </span>
            {GAMES.map(g => {
              const isSelected = selectedGame === g;
              return (
                <button
                  key={g}
                  type="button"
                  onClick={() => setSelectedGame(g)}
                  style={{
                    padding: '3px 12px',
                    borderRadius: 'var(--radius-pills)',
                    fontSize: '11px',
                    fontWeight: isSelected ? 600 : 500,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                    background: isSelected ? 'rgba(34, 211, 238, 0.15)' : 'transparent',
                    color: isSelected ? 'var(--cyan)' : 'var(--text2)',
                    fontFamily: 'var(--font-geistmono)'
                  }}
                >
                  {g}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* FEED CONTENT */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
          <p style={{ color: 'var(--text2)', fontSize: '14px' }}>Fetching latest competitive updates...</p>
        </div>
      ) : error ? (
        <div className="glassCard" style={{ padding: '36px', textAlign: 'center', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <p style={{ color: '#f87171', marginBottom: '16px' }}>{error}</p>
          <button type="button" className="secondaryBtn" onClick={fetchNews}>
            Retry Feed
          </button>
        </div>
      ) : articles.length === 0 ? (
        <div className="glassCard" style={{
          padding: '48px 24px',
          textAlign: 'center',
        }}>
          <Gamepad2 size={36} color="var(--text2)" style={{ marginBottom: '12px' }} />
          <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, marginBottom: '6px', fontFamily: "'Space Grotesk', sans-serif" }}>No updates found</h3>
          <p style={{ color: 'var(--text2)', fontSize: '13px', maxWidth: '420px', margin: '0 auto 16px' }}>
            There are currently no updates matching {selectedGame !== 'All' ? selectedGame : 'this filter'}. Check back shortly or reset your filters.
          </p>
          <button
            type="button"
            className="glassBtn"
            onClick={() => { setSelectedGame('All'); setSelectedCategory('All'); }}
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '16px'
        }}>
          {articles.map((item) => {
            const catStyle = getCategoryColor(item.category);
            return (
              <div 
                key={item.id} 
                className="glassCard"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  padding: 0,
                  transition: 'transform var(--transition-fast), border-color var(--transition-fast)'
                }}
              >
                {item.image_url ? (
                  <div style={{ height: '160px', overflow: 'hidden', position: 'relative', borderBottom: '1px solid var(--border)' }}>
                    <img 
                      src={item.image_url} 
                      alt={item.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      left: '12px',
                      display: 'flex',
                      gap: '6px'
                    }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-pills)',
                        fontSize: '11px',
                        fontFamily: 'var(--font-geistmono)',
                        fontWeight: 600,
                        background: catStyle.bg,
                        color: catStyle.color,
                        border: `1px solid ${catStyle.border}`
                      }}>
                        {item.category}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    height: '50px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderBottom: '1px solid var(--border)',
                    padding: '10px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-pills)',
                      fontSize: '11px',
                      fontFamily: 'var(--font-geistmono)',
                      fontWeight: 600,
                      background: catStyle.bg,
                      color: catStyle.color,
                      border: `1px solid ${catStyle.border}`
                    }}>
                      {item.category}
                    </span>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar size={12} />
                      {formatDate(item.published_at)}
                    </span>
                  </div>
                )}

                <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: 'var(--cyan)',
                      fontFamily: 'var(--font-geistmono)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em'
                    }}>
                      {item.game}
                    </span>
                    {item.image_url && (
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)' }}>
                        • {formatDate(item.published_at)}
                      </span>
                    )}
                  </div>

                  <h3 style={{
                    fontSize: '16px',
                    fontWeight: 600,
                    color: '#ffffff',
                    marginBottom: '8px',
                    lineHeight: 1.35,
                    fontFamily: "'Space Grotesk', sans-serif"
                  }}>
                    {item.title}
                  </h3>

                  <p style={{
                    color: 'var(--text2)',
                    fontSize: '13px',
                    lineHeight: 1.5,
                    marginBottom: '16px',
                    flex: 1
                  }}>
                    {item.summary}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
                    <button
                      type="button"
                      onClick={() => setActiveArticleModal(item)}
                      className="glassBtn"
                      style={{ fontSize: '12px', padding: '6px 14px' }}
                    >
                      Read Article
                    </button>

                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: 'var(--text2)',
                          fontSize: '11px',
                          fontFamily: 'var(--font-geistmono)',
                          textDecoration: 'none'
                        }}
                      >
                        <span>Official Source</span>
                        <ExternalLink size={11} color="var(--cyan)" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* READ FULL ARTICLE MODAL */}
      {activeArticleModal && (
        <div className="modalOverlay" onClick={() => setActiveArticleModal(null)} style={{ zIndex: 1000 }}>
          <div
            className="modalContainer glassCard"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '680px',
              maxHeight: '85vh',
              overflowY: 'auto'
            }}
          >
            <button
              type="button"
              className="modalCloseBtn"
              onClick={() => setActiveArticleModal(null)}
            >
              <X size={20} />
            </button>

            <div style={{ textAlign: 'left', marginBottom: '20px' }}>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                <span className="matchBadge" style={{ background: 'rgba(34, 211, 238, 0.15)', color: 'var(--cyan)' }}>
                  {activeArticleModal.game}
                </span>
                <span className="matchBadge">
                  {activeArticleModal.category}
                </span>
              </div>
              <h2 style={{ fontSize: '22px', fontWeight: 600, color: '#ffffff', margin: '4px 0 8px 0', fontFamily: "'Space Grotesk', sans-serif" }}>
                {activeArticleModal.title}
              </h2>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text-muted)' }}>
                Published on {formatDate(activeArticleModal.published_at)}
              </span>
            </div>

            {activeArticleModal.image_url && (
              <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', marginBottom: '16px', maxHeight: '240px', border: '1px solid var(--border)' }}>
                <img
                  src={activeArticleModal.image_url}
                  alt={activeArticleModal.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            )}

            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '14px 18px',
              borderRadius: 'var(--radius-md)',
              borderLeft: '3px solid var(--cyan)',
              borderTop: '1px solid var(--border)',
              borderRight: '1px solid var(--border)',
              borderBottom: '1px solid var(--border)',
              marginBottom: '16px',
              textAlign: 'left'
            }}>
              <strong style={{ color: '#ffffff', fontSize: '11px', display: 'block', marginBottom: '4px', fontFamily: 'var(--font-geistmono)' }}>
                SUMMARY
              </strong>
              <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0, lineHeight: 1.5 }}>
                {activeArticleModal.summary}
              </p>
            </div>

            {activeArticleModal.content ? (
              <div style={{ color: 'var(--text2)', fontSize: '13px', lineHeight: 1.6, whiteSpace: 'pre-line', marginBottom: '20px', textAlign: 'left' }}>
                {activeArticleModal.content}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '12px', fontStyle: 'italic', marginBottom: '20px', fontFamily: 'var(--font-geistmono)', textAlign: 'left' }}>
                Full patch notes details available via the official publisher link below.
              </p>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
              {activeArticleModal.source_url ? (
                <a
                  href={activeArticleModal.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="primaryBtn"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '8px 16px', textDecoration: 'none', fontSize: '12px' }}
                >
                  <span>Visit Publisher Portal</span>
                  <ExternalLink size={13} />
                </a>
              ) : <div />}

              <button
                type="button"
                className="glassBtn"
                onClick={() => setActiveArticleModal(null)}
                style={{ padding: '8px 18px', fontSize: '12px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE ARTICLE MODAL (ADMIN ONLY) */}
      <CreateArticleModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onArticleCreated={handleArticleCreated}
      />
    </div>
  );
}

export default NewsHub;
