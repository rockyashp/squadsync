import React, { useState } from 'react';
import { Crown, Users, Check, Send, Sparkles } from 'lucide-react';

const INITIAL_LOBBIES = [
  {
    id: 1,
    title: 'Immortal Radiant Push',
    game: 'VALORANT',
    needs: 'Needs Controller / Support',
    capacity: '3/4 Players',
    matchScore: 96,
  },
  {
    id: 2,
    title: 'Apex Predator Grind',
    game: 'Apex Legends',
    needs: 'Needs Entry Fragger',
    capacity: '2/3 Players',
    matchScore: 92,
  },
  {
    id: 3,
    title: 'R6 Champion Defense',
    game: 'Rainbow Six',
    needs: 'Needs Anchor / Sentinel',
    capacity: '4/5 Players',
    matchScore: 94,
  },
];

export default function Step3SquadMode({ onSelectCreate, selectedGame }) {
  const [showLobbies, setShowLobbies] = useState(false);
  const [requestedLobbies, setRequestedLobbies] = useState({});

  const handleRequestJoin = (lobbyId) => {
    setRequestedLobbies((prev) => ({
      ...prev,
      [lobbyId]: true,
    }));
  };

  return (
    <div className="onboardingStep">
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 className="sectionTitle" style={{ marginBottom: '8px' }}>
          STEP 3: SQUAD SETUP
        </h2>
        <p className="sectionSubtitle">
          Would you like to build a new squad or join active lobbies for {selectedGame}?
        </p>
      </div>

      <div className="actionChoiceGrid" style={{ maxWidth: '980px', margin: '0 auto' }}>
        {/* CREATE SQUAD CARD */}
        <div className="actionCard" onClick={onSelectCreate}>
          <div className="actionIcon">
            <Crown size={28} />
          </div>
          <h3>Create New Squad</h3>
          <p>
            Form a brand new squad as Team Leader. AI will automatically curate free agent candidates
            that complement your Gamer DNA™ and eliminate tilt.
          </p>
          <button type="button" className="primaryBtn" style={{ marginTop: 'auto' }}>
            Build New Squad &rarr;
          </button>
        </div>

        {/* JOIN EXISTING LOBBIES CARD */}
        <div
          className="actionCard"
          onClick={() => setShowLobbies((prev) => !prev)}
          style={{
            borderColor: showLobbies ? 'var(--cyan)' : 'rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="actionIcon" style={{ color: 'var(--violet)', background: 'rgba(139, 92, 246, 0.1)' }}>
            <Users size={28} />
          </div>
          <h3>Join Existing Lobbies</h3>
          <p>
            Browse active live demo lobbies looking for players matching your preferred role,
            communication style, and gaming schedule.
          </p>
          <button type="button" className="glassBtn" style={{ marginTop: 'auto' }}>
            {showLobbies ? 'Hide Active Lobbies' : 'Browse Active Lobbies'}
          </button>
        </div>
      </div>

      {/* DEMO LOBBIES DISPLAY */}
      {showLobbies && (
        <div
          className="glassCard lobbyContainer"
          style={{
            maxWidth: '980px',
            margin: '36px auto 0',
            padding: '28px',
            textAlign: 'left',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Sparkles size={18} color="var(--cyan)" />
            <h3 style={{ fontSize: '18px', color: '#fff', margin: 0 }}>
              Active Demo Lobbies Matching Your DNA
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {INITIAL_LOBBIES.map((lobby) => {
              const isSent = requestedLobbies[lobby.id];
              return (
                <div key={lobby.id} className="lobbyCardItem">
                  <div className="lobbyTitleInfo">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <h4>{lobby.title}</h4>
                      <span className="matchBadge" style={{ background: 'rgba(46, 213, 115, 0.15)', color: '#2ed573', borderColor: '#2ed573' }}>
                        {lobby.matchScore}% Match
                      </span>
                    </div>
                    <p>
                      {lobby.game} • {lobby.needs} • <span style={{ color: 'var(--cyan)' }}>{lobby.capacity}</span>
                    </p>
                  </div>

                  <button
                    type="button"
                    className="primaryBtn"
                    onClick={() => handleRequestJoin(lobby.id)}
                    disabled={isSent}
                    style={{
                      background: isSent ? '#2ed573' : undefined,
                      borderColor: isSent ? '#2ed573' : undefined,
                      color: isSent ? '#000' : undefined,
                    }}
                  >
                    {isSent ? (
                      <>
                        <Check size={16} /> Join Request Sent!
                      </>
                    ) : (
                      <>
                        <Send size={15} /> Request Join
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
