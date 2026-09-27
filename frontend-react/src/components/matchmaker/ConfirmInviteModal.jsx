import React, { useState } from 'react';
import { X, Users, Send, CheckCircle2, Trophy } from 'lucide-react';
import { squadsApi } from '../../api/squadsApi';
import { matchmakerApi } from '../../api/matchmakerApi';

export default function ConfirmInviteModal({ isOpen, onClose, squad, selectedGame, synergyScore, onBroadcastComplete }) {
  const [broadcasting, setBroadcasting] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setBroadcasting(true);
    try {
      // Create team in backend
      const teamData = {
        name: `${selectedGame} Strike Force ${Math.floor(100 + Math.random() * 900)}`,
        game: selectedGame,
        description: `Formed via Matchmaker with ${squad.length} drafted players.`,
        synergy_score: Number(synergyScore) || 88.0,
      };

      await squadsApi.createSquad(teamData);
      await matchmakerApi.recommendSquad(squad.map((p) => p.id));
    } catch (err) {
      console.warn('Backend team sync or recommendation fallback:', err);
    }

    setBroadcasting(false);
    onClose();
    onBroadcastComplete(squad.map((p) => p.name).join(', '));
  };

  return (
    <div className="modalOverlay" onClick={onClose}>
      <div className="modalContainer glassCard" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px' }}>
        <button type="button" className="modalCloseBtn" onClick={onClose}>
          <X size={20} />
        </button>

        <div style={{ textAlign: 'left', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="matchBadge" style={{ background: 'rgba(34, 211, 238, 0.2)', color: 'var(--cyan)', borderColor: 'var(--cyan)' }}>
              {selectedGame}
            </span>
            <span className="matchBadge" style={{ background: 'rgba(139, 92, 246, 0.2)', color: 'var(--violet)', borderColor: 'var(--violet)' }}>
              <Trophy size={12} style={{ marginRight: '4px' }} />
              Predicted Synergy: {synergyScore}%
            </span>
          </div>

          <h2 style={{ fontSize: '24px', color: '#fff', margin: '0 0 6px 0' }}>
            Broadcast Squad Invitations
          </h2>
          <p style={{ color: 'var(--text2)', fontSize: '14px', margin: 0, lineHeight: 1.5 }}>
            Send real-time match requests to the following {squad.length} drafted candidates:
          </p>
        </div>

        {/* ROSTER LIST */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '28px' }}>
          {squad.map((player) => (
            <div
              key={player.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 16px',
                background: 'rgba(255, 255, 255, 0.04)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
              }}
            >
              <div>
                <strong style={{ color: '#fff', display: 'block', fontSize: '15px' }}>
                  {player.name}
                </strong>
                <span className={`roleBadge ${player.role.toLowerCase()}`} style={{ marginTop: '4px', display: 'inline-block' }}>
                  {player.role}
                </span>
              </div>

              <span className="matchBadge" style={{ background: 'rgba(46, 213, 115, 0.15)', color: '#2ed573', borderColor: '#2ed573' }}>
                {player.match}% Match
              </span>
            </div>
          ))}
        </div>

        {/* BUTTONS */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button type="button" className="glassBtn" onClick={onClose} disabled={broadcasting}>
            Cancel
          </button>
          <button
            type="button"
            className="primaryBtn"
            onClick={handleConfirm}
            disabled={broadcasting}
            style={{ padding: '12px 24px' }}
          >
            {broadcasting ? (
              'Broadcasting Invitations...'
            ) : (
              <>
                <Send size={16} /> Confirm & Send Invites
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
