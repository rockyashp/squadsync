import React from 'react';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

const GAMES = [
  { id: 'VALORANT', name: 'VALORANT', logo: '/assets/game-logo/VALO.png', tag: 'Tactical 5v5 FPS' },
  { id: 'Apex Legends', name: 'Apex Legends', logo: '/assets/game-logo/APEX Legends.png', tag: 'Battle Royale Trios' },
  { id: 'CS2', name: 'CS2', logo: '/assets/game-logo/CS2.png', tag: 'Defuse 5v5' },
  { id: 'Rainbow Six Siege', name: 'Rainbow Six', logo: '/assets/game-logo/Rainbow Six.png', tag: 'Siege & Breach' },
  { id: 'Call of Duty', name: 'Call of Duty', logo: '/assets/game-logo/COD.png', tag: 'Warzone & Resurgence' },
];

export default function Step2SelectGame({ selectedGame, onSelectGame, onContinue }) {
  return (
    <div className="onboardingStep">
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 className="sectionTitle" style={{ marginBottom: '8px' }}>
          STEP 2: CHOOSE YOUR PRIMARY GAME
        </h2>
        <p className="sectionSubtitle">
          Select the competitive title you want AI matchmaking and squad drafting for.
        </p>
      </div>

      <div className="gameSelectGrid" style={{ maxWidth: '1100px', margin: '0 auto' }}>
        {GAMES.map((game) => {
          const isSelected = selectedGame === game.id;
          return (
            <div
              key={game.id}
              className={`gameCardSelect ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectGame(game.id)}
            >
              <img src={game.logo} alt={game.name} />
              <h3>{game.name}</h3>
              <span style={{
                color: isSelected ? 'var(--cyan)' : 'var(--text-muted)',
                fontSize: '12px',
                marginTop: '6px',
                fontWeight: 500,
              }}>
                {game.tag}
              </span>
              {isSelected && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  color: 'var(--cyan)',
                  fontSize: '12px',
                  fontWeight: 700,
                  marginTop: '12px',
                }}>
                  <CheckCircle2 size={14} /> Selected
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ textAlign: 'center', marginTop: '40px' }}>
        <button
          type="button"
          className="primaryBtn largeBtn"
          onClick={onContinue}
          style={{ padding: '14px 36px', fontSize: '15px' }}
        >
          Confirm {selectedGame} & Proceed <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}
