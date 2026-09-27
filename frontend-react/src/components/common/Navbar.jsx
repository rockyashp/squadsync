import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut } from 'lucide-react';
import logoImg from '../../assets/logo.png';

export default function Navbar({ backendHealth, activeTab, onSelectTab }) {
  const { user, isAuthenticated, isAdmin, openLoginModal, openRegisterModal, logout } = useAuth();

  const gamerTag = user?.gamer_tag || user?.username || user?.email?.split('@')[0] || 'Gamer';
  const initials = gamerTag.substring(0, 2).toUpperCase();

  return (
    <nav id="navbar">
      {/* BRAND LOGO: CUSTOM LOGO ASSET */}
      <a href="#hero" className="logo" onClick={() => onSelectTab && onSelectTab('overview')}>
        <img 
          src={logoImg} 
          alt="SquadSync Logo" 
          className="brandLogoImg"
        />
        <h2 style={{ fontSize: '20px', margin: 0, fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, color: '#ffffff', letterSpacing: '-0.3px' }}>
          Squad<span style={{ color: 'var(--cyan)' }}>Sync</span>
        </h2>
      </a>

      {/* NAV LINKS (FROM REFERENCE) */}
      <ul id="navMenu">
        <li>
          <a href="#hero" onClick={() => onSelectTab && onSelectTab('overview')}>Overview</a>
        </li>
        <li>
          <a href="#games" onClick={() => onSelectTab && onSelectTab('overview')}>Games</a>
        </li>
        <li>
          <a href="#features" onClick={() => onSelectTab && onSelectTab('overview')}>Features</a>
        </li>
        <li>
          <a href="#reviews" onClick={() => onSelectTab && onSelectTab('overview')}>Reviews</a>
        </li>
      </ul>

      {/* ACTIONS & USER PROFILE (EXACT BUTTONS FROM REFERENCE) */}
      <div className="navButtons" id="navButtons">
        {/* API Status Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 10px',
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '9999px',
          fontSize: '11px',
          fontFamily: "'Outfit', sans-serif",
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: backendHealth?.status === 'healthy' ? '#10b981' : '#22d3ee',
            boxShadow: backendHealth?.status === 'healthy' ? '0 0 6px #10b981' : '0 0 6px #22d3ee',
          }} />
          <span style={{ color: '#94a3b8' }}>
            {backendHealth?.status === 'healthy' ? 'API Online' : 'Connecting'}
          </span>
        </div>

        {isAuthenticated ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* User Badge */}
            <div className="userBadge" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              background: 'rgba(34, 211, 238, 0.08)',
              border: '1px solid rgba(34, 211, 238, 0.3)',
              borderRadius: '12px',
              color: '#22d3ee',
              fontFamily: "'Space Grotesk', sans-serif",
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #22d3ee, #8b5cf6)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '11px',
                fontWeight: 700,
              }}>
                {initials}
              </div>
              <span style={{ fontSize: '14px', fontWeight: 600 }}>
                {gamerTag}
              </span>
              {isAdmin && (
                <span className="matchBadge" style={{
                  fontSize: '9px',
                  background: 'rgba(255, 99, 99, 0.15)',
                  borderColor: '#ff6363',
                  color: '#ff6363',
                }}>
                  ADMIN
                </span>
              )}
            </div>

            {/* Logout Button */}
            <button
              className="glassBtn logoutBtn"
              id="logoutBtn"
              onClick={logout}
              title="Sign Out"
            >
              <LogOut size={13} />
              <span>Logout</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="glassBtn"
              id="loginNavBtn"
              onClick={openLoginModal}
            >
              Login
            </button>
            <button
              className="primaryBtn"
              id="registerNavBtn"
              onClick={openRegisterModal}
            >
              Get Started
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
