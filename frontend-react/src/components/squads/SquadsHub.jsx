import React, { useState, useEffect } from 'react';
import { squadsApi } from '../../api/squadsApi';
import { useAuth } from '../../context/AuthContext';
import SquadCard from './SquadCard';
import CreateSquadModal from './CreateSquadModal';
import { Shield, Plus, RefreshCw, Loader2 } from 'lucide-react';

export default function SquadsHub({ onOpenSquadChat }) {
  const { user } = useAuth();
  const [squads, setSquads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchSquads = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    try {
      const res = await squadsApi.getMySquads();
      const squadList = res?.data?.data || res?.data || (Array.isArray(res) ? res : []);
      setSquads(squadList);
    } catch (err) {
      console.warn('Failed to fetch squads:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSquads();
  }, [user]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSquads();
  };

  const handleSquadCreated = (newSquad) => {
    setSquads((prev) => [newSquad, ...prev]);
    fetchSquads();
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'left' }}>
      {/* HEADER & ACTIONS */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: 600, color: '#ffffff', margin: 0, fontFamily: "'Space Grotesk', sans-serif" }}>
              Competitive Squads
            </h2>
            <span className="matchBadge">
              ROSTER SYNC
            </span>
          </div>
          <p style={{ color: 'var(--text2)', fontSize: '13px', margin: 0 }}>
            Manage persistent rosters, tactical roles, and predicted team chemistry.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="glassBtn"
            onClick={handleRefresh}
            disabled={refreshing || !user}
            style={{ padding: '6px 14px', fontSize: '12px' }}
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            className="primaryBtn"
            onClick={() => setIsCreateModalOpen(true)}
            disabled={!user}
            style={{ padding: '8px 18px', fontSize: '13px' }}
          >
            <Plus size={14} />
            <span>Create Squad</span>
          </button>
        </div>
      </div>

      {/* SQUADS GRID */}
      {loading ? (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text2)' }}>
          <Loader2 size={32} className="animate-spin" color="var(--cyan)" style={{ margin: '0 auto 12px' }} />
          <p style={{ margin: 0, fontSize: '13px', fontFamily: 'var(--font-geistmono)' }}>Loading competitive squads...</p>
        </div>
      ) : !user ? (
        <div
          className="glassCard"
          style={{
            padding: '48px 24px',
            textAlign: 'center',
          }}
        >
          <Shield size={36} color="var(--cyan)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, margin: '0 0 4px 0', fontFamily: "'Space Grotesk', sans-serif" }}>Authentication Required</h3>
          <p style={{ color: 'var(--text2)', fontSize: '13px', maxWidth: '420px', margin: '0 auto' }}>
            Sign in to view your competitive squad rosters and synergy scores.
          </p>
        </div>
      ) : squads.length === 0 ? (
        <div
          className="glassCard"
          style={{
            padding: '48px 24px',
            textAlign: 'center',
          }}
        >
          <Shield size={36} color="var(--text2)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: 600, margin: '0 0 4px 0', fontFamily: "'Space Grotesk', sans-serif" }}>No Active Squads Found</h3>
          <p style={{ color: 'var(--text2)', fontSize: '13px', maxWidth: '440px', margin: '0 auto 16px' }}>
            Form a new competitive squad or draft candidates through the AI Matchmaker to start competing.
          </p>
          <button
            type="button"
            className="primaryBtn"
            onClick={() => setIsCreateModalOpen(true)}
            style={{ padding: '8px 20px', fontSize: '13px' }}
          >
            <Plus size={14} /> Create Your First Squad
          </button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '16px'
        }}>
          {squads.map((squad) => (
            <SquadCard
              key={squad.id}
              squad={squad}
              onSquadUpdated={fetchSquads}
              onOpenSquadChat={onOpenSquadChat}
            />
          ))}
        </div>
      )}

      {/* CREATE SQUAD MODAL */}
      <CreateSquadModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSquadCreated={handleSquadCreated}
      />
    </div>
  );
}
