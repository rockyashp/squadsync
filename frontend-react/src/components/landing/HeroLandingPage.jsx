import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import logoImg from '../../assets/logo.png';

const GAMES = [
  { id: 'VALORANT', name: 'VALORANT', logo: '/assets/game-logo/VALO.png' },
  { id: 'Apex Legends', name: 'Apex Legends', logo: '/assets/game-logo/APEX Legends.png' },
  { id: 'Rainbow Six Siege', name: 'Rainbow Six Siege', logo: '/assets/game-logo/Rainbow Six.png' },
  { id: 'CS2', name: 'Counter Strike 2', logo: '/assets/game-logo/CS2.png' },
  { id: 'Call of Duty', name: 'Call of Duty', logo: '/assets/game-logo/COD.png' },
  { id: 'PUBG', name: 'PUBG', logo: '/assets/game-logo/pubg-logo.svg' },
];

const REVIEWS = [

];

export default function HeroLandingPage({ onGetStarted, onSelectGame }) {
  const { isAuthenticated, openRegisterModal } = useAuth();
  const [liveSynergy, setLiveSynergy] = useState('96%');
  const [mousePos, setMousePos] = useState({ x: -200, y: -200 });

  // Real-time live match synergy simulation (fluctuates between 95% and 98%)
  useEffect(() => {
    const timer = setInterval(() => {
      const randomSynergy = (95 + Math.random() * 3).toFixed(1);
      setLiveSynergy(`${randomSynergy}%`);
    }, 3800);
    return () => clearInterval(timer);
  }, []);

  // Ambient cursor glow tracker
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleActionClick = () => {
    if (isAuthenticated) {
      if (onGetStarted) onGetStarted();
    } else {
      openRegisterModal();
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', overflowX: 'hidden' }}>
      {/* CURSOR GLOW (From Reference) */}
      <div
        className="cursorGlow"
        id="cursorGlow"
        style={{
          left: `${mousePos.x}px`,
          top: `${mousePos.y}px`,
        }}
      />

      {/* =========================================
          HERO SECTION (EXACT REFERENCE REPLICA)
      ========================================= */}
      <section id="hero" className="hero">
        <div className="heroContent">
          {/* TAG */}
          <p className="tag">
            <svg viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4l3 3" />
            </svg>
            AI POWERED TEAMMATE MATCHMAKING
          </p>

          {/* MAIN HEADLINE */}
          <h1>
            DOMINATE<br />
            EVERY LOBBY.<br />
            <span>ZERO TOXICITY.</span>
          </h1>

          {/* HERO BODY TEXT */}
          <p className="heroText">
            Squad Sync analyzes your Gamer DNA™, communication style, competitive mindset, preferred roles, schedule, and playstyle to build the perfect squad in seconds.
          </p>

          {/* HERO BUTTONS */}
          <div className="heroButtons">
            <button
              type="button"
              className="primaryBtn largeBtn"
              id="heroGetStartedBtn"
              onClick={handleActionClick}
            >
              {isAuthenticated ? 'Enter AI Matchmaker' : 'Create Free Profile'}
            </button>
          </div>

          {/* STATS ROW */}
          <div className="stats">
            <div className="glassCard stat">
              <h2 id="statAccuracy">98.4%</h2>
              <p>Match Accuracy</p>
            </div>

            <div className="glassCard stat">
              <h2>&lt;3s</h2>
              <p>AI Speed</p>
            </div>

            <div className="glassCard stat">
              <h2>0%</h2>
              <p>Role Conflicts</p>
            </div>
          </div>
        </div>

        {/* HERO RIGHT (FLOATING CONTROLLER & LIVE ANALYSIS CARD) */}
        <div className="heroRight">
          {/* FLOATING CONTROLLER MOVED HIGH UP (EXACT REFERENCE SPEC) */}
          <div className="controllerFloat">
            <img src="/assets/Controller.png" alt="Squad Sync Controller" />
          </div>

          {/* PREVIEW CARD: LIVE MATCH ANALYSIS */}
          <div className="previewCard glassCard">
            <div className="liveHeader">
              <div className="liveDot" />
              <h4>LIVE MATCH ANALYSIS</h4>
            </div>

            <div className="matchScore">
              <div>
                <h1 id="squadScore">13</h1>
                <p>Your Squad</p>
              </div>
              <div className="divider" />
              <div>
                <h1 id="enemyScore">8</h1>
                <p>Enemy</p>
              </div>
            </div>

            <div className="progress">
              <div className="progressFill" id="liveMatchProgress" style={{ width: '96%' }} />
            </div>

            <div className="matchInfo">
              <p>Team Synergy <strong id="heroSynergy">{liveSynergy}</strong></p>
              <p>Voice Coordination <strong>Excellent</strong></p>
              <p>Tilt Risk <strong>Low</strong></p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================
          SUPPORTED GAMES SECTION (FROM REFERENCE)
      ========================================= */}
      <section id="games">
        <h2 className="sectionTitle">SUPPORTED GAMES</h2>
        <p className="sectionSubtitle">Cross-platform intelligence optimized for competitive titles.</p>

        <div className="gameScroller">
          {GAMES.map((game) => (
            <div
              key={game.id}
              className="game glassCard"
              onClick={() => onSelectGame && onSelectGame(game.id)}
              title={`Matchmake in ${game.name}`}
            >
              <div className="gameIcon">
                <img src={game.logo} alt={`${game.name} Logo`} />
              </div>
              {game.name}
            </div>
          ))}
        </div>
      </section>

      {/* =========================================
          FEATURES SECTION (WHY SQUAD SYNC?)
      ========================================= */}
      
      {/* =========================================
          TESTIMONIALS / REVIEWS SECTION
      ========================================= */}
      
      {/* =========================================
          CALL TO ACTION (CTA)
      ========================================= */}
      <section className="cta">
        <div className="glassCard ctaBox">
          <h2>Ready to Build Your Dream Squad?</h2>
          <p>Join thousands of competitive gamers using AI-powered matchmaking every single day.</p>
          <button
            type="button"
            className="primaryBtn largeBtn"
            onClick={handleActionClick}
          >
            {isAuthenticated ? 'Launch AI Matchmaker' : 'Create Free Profile'}
          </button>
        </div>
      </section>

      {/* =========================================
          FOOTER
      ========================================= */}
      <footer>
        <div className="footerLogo" style={{ display: 'inline-flex', alignItems: 'center', gap: '12px' }}>
          <img 
            src={logoImg} 
            alt="SquadSync Logo" 
            style={{ 
              height: '36px', 
              width: 'auto', 
              objectFit: 'contain',
              filter: 'drop-shadow(0 0 14px rgba(34, 211, 238, 0.45))' 
            }} 
          />
          <span>Squad<span style={{ color: 'var(--cyan)' }}>Sync</span></span>
        </div>
        <div className="footerLinks">
          <a href="#hero">Overview</a>
          <a href="#games">Games</a>
          <a href="#features">Features</a>
          <a href="#reviews">Reviews</a>
          <a href="https://discord.gg" target="_blank" rel="noopener noreferrer">Join Discord</a>
          <a href="#">Support</a>
        </div>
        <p>© 2026 Squad Sync. Built for Competitive Gamers.</p>
      </footer>
    </div>
  );
}
