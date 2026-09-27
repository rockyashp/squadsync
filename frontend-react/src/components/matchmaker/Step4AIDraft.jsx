import React, { useState, useEffect } from 'react';
import { matchmakerApi } from '../../api/matchmakerApi';
import ConfirmInviteModal from './ConfirmInviteModal';
import { Users, Bot, UserPlus, X, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

const CANDIDATES_POOL = [
  { id: '1', name: 'Shadow', role: 'Duelist', desc: 'Aggressive Entry', match: 96 },
  { id: '2', name: 'Nova', role: 'Controller', desc: 'Smoke Specialist', match: 94 },
  { id: '3', name: 'Ghost', role: 'Sentinel', desc: 'Anchor & Defense', match: 91 },
  { id: '4', name: 'Echo', role: 'Initiator', desc: 'Recon & Flash Comms', match: 95 },
  { id: '5', name: 'Venom', role: 'Duelist', desc: 'Flanker & Lurker', match: 88 },
  { id: '6', name: 'Valkyrie', role: 'Initiator', desc: 'High Comms IGL', match: 93 },
];

export default function Step4AIDraft({ selectedGame }) {
  const [bench, setBench] = useState(CANDIDATES_POOL);
  const [squad, setSquad] = useState([]);
  const [synergyScore, setSynergyScore] = useState(0);
  const [recommendation, setRecommendation] = useState('Draft players from the pool to analyze squad role synergy.');
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [broadcastFeedback, setBroadcastFeedback] = useState(null);

  // Calculate synergy whenever squad changes
  useEffect(() => {
    async function evaluate() {
      if (squad.length === 0) {
        setSynergyScore(0);
        setRecommendation('Draft players from the pool to analyze squad role synergy.');
        return;
      }

      const rolesCount = {};
      squad.forEach((p) => {
        rolesCount[p.role] = (rolesCount[p.role] || 0) + 1;
      });
      const uniqueRoles = Object.keys(rolesCount).length;

      let score = 0;
      if (squad.length === 1) score = 35;
      else if (squad.length === 2) score = uniqueRoles === 2 ? 65 : 50;
      else if (squad.length === 3) score = uniqueRoles === 3 ? 84 : 70;
      else if (squad.length === 4) {
        if (uniqueRoles === 4) score = 98;
        else if (uniqueRoles === 3) score = 88;
        else score = 72;
      }

      // Try calling backend API for neural chemistry calculation
      try {
        const res = await matchmakerApi.evaluateTeam({
          roles: squad.map((s) => s.role),
          player_ids: squad.map((s) => s.id),
        });
        if (res.data?.synergy_score) {
          score = Math.round(res.data.synergy_score);
        }
      } catch (err) {
        // Local calculation fallback
      }

      setSynergyScore(score);

      // Intelligent recommendation text
      if (squad.length < 4) {
        const needed = 4 - squad.length;
        setRecommendation(`Draft ${needed} more player${needed > 1 ? 's' : ''} to optimize full team chemistry.`);
      } else if (uniqueRoles === 4) {
        setRecommendation('Perfect Composition! All 4 core roles (Duelist, Controller, Sentinel, Initiator) covered with zero tilt risk.');
      } else if (rolesCount['Duelist'] > 1) {
        setRecommendation('High Duelist density detected. Consider swapping one Duelist for a Controller or Initiator for balanced utility.');
      } else {
        setRecommendation('Strong team foundation. Squad synergy is high and primed for competitive queue.');
      }
    }

    evaluate();
  }, [squad]);

  const handleAddPlayer = (candidate) => {
    if (squad.length >= 4) {
      alert('Squad is full! Remove a player to add a new candidate.');
      return;
    }
    if (squad.some((p) => p.id === candidate.id)) return;

    setSquad((prev) => [...prev, candidate]);
  };

  const handleRemoveSlot = (index) => {
    setSquad((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleBroadcastComplete = (playerNames) => {
    setBroadcastFeedback(`Real-time notifications sent to ${playerNames}. Awaiting lobby acceptances.`);
    setTimeout(() => {
      setBroadcastFeedback(null);
    }, 7000);
  };

  return (
    <div className="onboardingStep">
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 className="sectionTitle" style={{ marginBottom: '8px' }}>
          STEP 4: AI SQUAD DRAFT & MATCHMAKING
        </h2>
        <p className="sectionSubtitle">
          Draft compatible free agents for <strong>{selectedGame}</strong> to analyze live chemistry and broadcast join requests.
        </p>
      </div>

      <div className="builderLayout">
        {/* FREE AGENTS CANDIDATES BENCH */}
        <div className="glassCard playersBench">
          <h3>
            <Bot size={22} color="var(--cyan)" />
            Recommended Free Agent Pool
          </h3>

          <div className="playerCardList">
            {bench.map((candidate) => {
              const isDrafted = squad.some((p) => p.id === candidate.id);
              return (
                <div key={candidate.id} className="playerCard">
                  <div className="playerInfo">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <h4>{candidate.name}</h4>
                      <span className="matchBadge" style={{ background: 'rgba(46, 213, 115, 0.15)', color: '#2ed573', borderColor: '#2ed573' }}>
                        {candidate.match}% Match
                      </span>
                    </div>
                    <p>
                      {candidate.role} • {candidate.desc}
                    </p>
                  </div>

                  <button
                    type="button"
                    className="addPlayerBtn"
                    onClick={() => handleAddPlayer(candidate)}
                    disabled={isDrafted}
                  >
                    {isDrafted ? 'Added' : 'Add to Squad'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* ACTIVE SQUAD ROSTER & SYNERGY METER */}
        <div className="glassCard squadArea">
          <h3>
            <Users size={22} color="var(--cyan)" />
            Your Active Squad Roster (4 Slots)
          </h3>

          <div id="teamSlots">
            {[0, 1, 2, 3].map((index) => {
              const player = squad[index];
              if (player) {
                return (
                  <div key={index} className="slot filled">
                    <h4>{player.name}</h4>
                    <p>{player.role}</p>
                    <button
                      type="button"
                      className="removeSlotBtn"
                      onClick={() => handleRemoveSlot(index)}
                      title="Remove from squad"
                    >
                      &times;
                    </button>
                  </div>
                );
              }
              return (
                <div key={index} className="slot">
                  Empty Slot
                </div>
              );
            })}
          </div>

          {/* SYNERGY METER */}
          <div className="synergyBox">
            <h2>Predicted Squad Synergy</h2>
            <div className="bigScore">{synergyScore}%</div>

            <div className="progressLarge">
              <div
                style={{
                  height: '100%',
                  width: `${synergyScore}%`,
                  background: 'linear-gradient(90deg, var(--cyan), var(--violet))',
                  borderRadius: 'var(--radius-full)',
                  transition: 'width 0.8s ease',
                  boxShadow: '0 0 15px var(--cyan-glow)',
                }}
              />
            </div>

            <div className="recommendation">
              <strong>AI Recommendation</strong>
              <p>{recommendation}</p>
            </div>

            <button
              type="button"
              className="primaryBtn largeBtn fullWidth"
              onClick={() => {
                if (squad.length === 0) {
                  alert('Please draft at least one player into your roster before sending join requests!');
                  return;
                }
                setIsConfirmModalOpen(true);
              }}
              style={{ marginTop: '22px' }}
            >
              Send Join Request to All Selected Players
            </button>

            {broadcastFeedback && (
              <div
                className="glassCard"
                style={{
                  marginTop: '16px',
                  padding: '16px 20px',
                  borderColor: '#2ed573',
                  background: 'rgba(46, 213, 115, 0.12)',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: '#2ed573',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#000',
                      fontWeight: 'bold',
                      flexShrink: 0,
                    }}
                  >
                    ✓
                  </div>
                  <div>
                    <h4 style={{ color: '#2ed573', margin: 0, fontSize: '15px', fontWeight: 700 }}>
                      Squad Join Requests Broadcasted!
                    </h4>
                    <p style={{ color: 'var(--text2)', margin: '4px 0 0 0', fontSize: '13px' }}>
                      {broadcastFeedback}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CONFIRMATION MODAL */}
      <ConfirmInviteModal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        squad={squad}
        selectedGame={selectedGame}
        synergyScore={synergyScore}
        onBroadcastComplete={handleBroadcastComplete}
      />
    </div>
  );
}
