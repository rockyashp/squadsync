import React, { useState } from 'react';
import { Search, UserPlus, Check, X, Loader2 } from 'lucide-react';
import { friendsApi } from '../../api/friendsApi';

export default function FriendSearch({ onRequestSent }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sentMap, setSentMap] = useState({});
  const [isOpen, setIsOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setErrorMsg('');
    try {
      const res = await friendsApi.searchGamers(query.trim());
      const players = res.data?.data || res.data || [];
      setResults(players);
      setIsOpen(true);
    } catch (err) {
      setErrorMsg('No players found or search query failed.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (targetUserId) => {
    try {
      await friendsApi.sendFriendRequest(targetUserId);
      setSentMap((prev) => ({ ...prev, [targetUserId]: true }));
      if (onRequestSent) onRequestSent();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to send friend request.';
      alert(msg);
    }
  };

  return (
    <div style={{ marginBottom: '20px', position: 'relative' }}>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search competitive gamers by username or gamer tag..."
            style={{
              width: '100%',
              boxSizing: 'border-box',
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-buttons)',
              padding: '10px 14px 10px 38px',
              color: '#ffffff',
              fontSize: '13px',
              outline: 'none',
              transition: 'border-color var(--transition-fast)'
            }}
          />
          <Search
            size={16}
            color="var(--cyan)"
            style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }}
          />
        </div>

        <button type="submit" className="primaryBtn" disabled={loading} style={{ padding: '8px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          <span>Search</span>
        </button>
      </form>

      {/* SEARCH RESULTS DROPDOWN */}
      {isOpen && (
        <div
          className="glassCard"
          style={{
            marginTop: '10px',
            padding: '18px',
            textAlign: 'left',
            borderRadius: 'var(--radius-cards)',
            background: 'rgba(13, 19, 33, 0.96)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85), 0 0 30px rgba(34, 211, 238, 0.15)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--cyan)', margin: 0, fontSize: '11px', fontFamily: 'var(--font-geistmono)', fontWeight: 600 }}>
              SEARCH RESULTS ({results.length})
            </span>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', padding: '4px' }}
            >
              <X size={16} />
            </button>
          </div>

          {errorMsg && (
            <p style={{ color: '#f87171', fontSize: '12px', margin: 0 }}>{errorMsg}</p>
          )}

          {results.length === 0 && !errorMsg ? (
            <p style={{ color: 'var(--text2)', fontSize: '12px', margin: 0, fontFamily: 'var(--font-geistmono)' }}>
              No matching gamers found for "{query}".
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {results.map((player) => {
                const isSent = sentMap[player.user_id] || player.friendship_status === 'PENDING_SENT';
                const isAlreadyFriends = player.friendship_status === 'ACCEPTED';

                return (
                  <div
                    key={player.user_id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 14px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div
                        style={{
                          width: '34px',
                          height: '34px',
                          borderRadius: 'var(--radius-sm)',
                          background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.2))',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '12px',
                          fontWeight: 700,
                          color: '#ffffff',
                          fontFamily: "'Space Grotesk', sans-serif"
                        }}
                      >
                        {(player.gamer_tag || player.username || 'G').substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <strong style={{ color: '#ffffff', fontSize: '13px', display: 'block', fontWeight: 600, fontFamily: "'Space Grotesk', sans-serif" }}>
                          {player.gamer_tag || player.username}
                        </strong>
                        <div style={{ display: 'flex', gap: '6px', marginTop: '2px' }}>
                          {player.primary_role && (
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: 'var(--radius-pills)',
                              background: 'rgba(34, 211, 238, 0.1)',
                              border: '1px solid rgba(34, 211, 238, 0.25)',
                              color: 'var(--cyan)',
                              fontSize: '10px',
                              fontFamily: 'var(--font-geistmono)'
                            }}>
                              {player.primary_role}
                            </span>
                          )}
                          {player.rank_tier && (
                            <span style={{ fontSize: '11px', color: 'var(--text2)', fontFamily: 'var(--font-geistmono)' }}>
                              • {player.rank_tier}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div>
                      {isAlreadyFriends ? (
                        <span style={{
                          padding: '3px 10px',
                          borderRadius: 'var(--radius-pills)',
                          fontSize: '11px',
                          fontFamily: 'var(--font-geistmono)',
                          background: 'rgba(16, 185, 129, 0.15)',
                          color: '#10b981',
                          border: '1px solid rgba(16, 185, 129, 0.4)'
                        }}>
                          FRIENDS
                        </span>
                      ) : isSent ? (
                        <span style={{
                          padding: '3px 10px',
                          borderRadius: 'var(--radius-pills)',
                          fontSize: '11px',
                          fontFamily: 'var(--font-geistmono)',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: 'var(--text2)',
                          border: '1px solid var(--border)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <Check size={11} color="var(--cyan)" /> SENT
                        </span>
                      ) : (
                        <button
                          type="button"
                          className="primaryBtn"
                          onClick={() => handleSendRequest(player.user_id)}
                          style={{ padding: '5px 12px', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                        >
                          <UserPlus size={13} /> Add Friend
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
