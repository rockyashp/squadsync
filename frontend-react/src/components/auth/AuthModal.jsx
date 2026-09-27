import React from 'react';
import { useAuth } from '../../context/AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import logoImg from '../../assets/logo.png';

export default function AuthModal() {
  const { isAuthModalOpen, authModalMode, closeAuthModal } = useAuth();

  if (!isAuthModalOpen) return null;

  return (
    <div
      className="modalOverlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) closeAuthModal();
      }}
    >
      <div className="glassCard modalContainer">
        <button
          className="modalCloseBtn"
          onClick={closeAuthModal}
          aria-label="Close modal"
        >
          &times;
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <img 
            src={logoImg} 
            alt="SquadSync Mascot Logo" 
            style={{ 
              height: '38px', 
              width: 'auto', 
              objectFit: 'contain',
              filter: 'drop-shadow(0 0 12px rgba(34, 211, 238, 0.45))' 
            }} 
          />
          <h3 style={{ fontSize: '18px', margin: 0, fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, color: '#ffffff', letterSpacing: '-0.3px' }}>
            Squad<span style={{ color: 'var(--cyan)' }}>Sync</span>
          </h3>
        </div>

        {authModalMode === 'login' ? <LoginForm /> : <RegisterForm />}
      </div>
    </div>
  );
}
