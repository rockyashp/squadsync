import React, { useState, useEffect } from 'react';
import apiClient from './api/client';
import { useAuth } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import AuthModal from './components/auth/AuthModal';
import HeroLandingPage from './components/landing/HeroLandingPage';
import MatchmakerDashboard from './components/matchmaker/MatchmakerDashboard';
import FriendsHub from './components/friends/FriendsHub';
import SquadsHub from './components/squads/SquadsHub';
import NewsHub from './components/news/NewsHub';
import AdminDashboard from './components/admin/AdminDashboard';
import ChatDrawer from './components/chat/ChatDrawer';
import { 
  Users, 
  Shield, 
  CheckCircle2,
  Bot,
  Newspaper,
  ShieldAlert,
  Sparkles
} from 'lucide-react';

function App() {
  const { user, isAuthenticated, isAdmin } = useAuth();
  const [backendHealth, setBackendHealth] = useState(null);
  const [activeTab, setActiveTab] = useState('matchmaker');
  const [activeChatTarget, setActiveChatTarget] = useState(null);

  const handleOpenChat = (target) => {
    setActiveChatTarget(target);
  };

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await apiClient.get('/../../health');
        setBackendHealth(res?.data || res);
      } catch (err) {
        setBackendHealth({ status: 'offline' });
      }
    }
    checkHealth();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', background: 'var(--bg)' }}>
      {/* NAVBAR (REFERENCE DESIGN) */}
      <Navbar 
        backendHealth={backendHealth} 
        activeTab={activeTab} 
        onSelectTab={setActiveTab} 
      />

      {/* AUTHENTICATION MODAL */}
      <AuthModal />

      {/* MAIN CONTAINER */}
      {!isAuthenticated ? (
        /* UNAUTHENTICATED VISITOR: STANDALONE HERO LANDING PAGE */
        <main style={{ flex: 1, width: '100%' }}>
          <HeroLandingPage 
            onGetStarted={() => setActiveTab('matchmaker')} 
            onSelectGame={() => setActiveTab('matchmaker')} 
          />
        </main>
      ) : (
        /* AUTHENTICATED USER: COCKPIT DASHBOARD OR OVERVIEW TAB */
        <main style={{ flex: 1, width: '100%', paddingBottom: '60px' }}>
          {/* OVERVIEW / HERO TAB */}
          {activeTab === 'overview' ? (
            <div>
              <div style={{ maxWidth: '1200px', margin: '20px auto 0', padding: '0 24px', textAlign: 'left' }}>
                <button
                  type="button"
                  className="primaryBtn"
                  onClick={() => setActiveTab('matchmaker')}
                  style={{ marginBottom: '16px' }}
                >
                  &larr; Back to AI Matchmaker
                </button>
              </div>
              <HeroLandingPage 
                onGetStarted={() => setActiveTab('matchmaker')} 
                onSelectGame={() => setActiveTab('matchmaker')} 
              />
            </div>
          ) : (
            <div style={{ maxWidth: '1200px', margin: '0 auto',marginTop: '80px', padding: '32px 24px', textAlign: 'center' }}>
              {/* LOGGED IN USER WELCOME BANNER */}
              <div className="glassCard" style={{
                padding: '20px 24px',
                marginBottom: '28px',
                textAlign: 'left',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '12px',
                      background: 'linear-gradient(135deg, #22d3ee, #8b5cf6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '15px',
                      fontWeight: 700,
                      color: '#ffffff',
                      fontFamily: "'Space Grotesk', sans-serif",
                      boxShadow: '0 0 15px rgba(34, 211, 238, 0.3)'
                    }}>
                      {(user?.gamer_tag || user?.username || 'G').substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h2 style={{ fontSize: '18px', color: '#ffffff', margin: 0, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', fontFamily: "'Space Grotesk', sans-serif" }}>
                        Welcome back, {user?.gamer_tag || user?.username}
                        {isAdmin && (
                          <span className="matchBadge" style={{
                            color: '#ff6363',
                            borderColor: 'rgba(255, 99, 99, 0.4)',
                            background: 'rgba(255, 99, 99, 0.15)'
                          }}>
                            ADMIN
                          </span>
                        )}
                      </h2>
                      <p style={{ color: '#94a3b8', fontSize: '13px', margin: '2px 0 0 0', fontFamily: "'Outfit', sans-serif" }}>
                        ID: <span style={{ color: '#ffffff' }}>{user?.id}</span> • {user?.email}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="glassBtn"
                      onClick={() => setActiveTab('overview')}
                      style={{ padding: '6px 14px', fontSize: '12px' }}
                    >
                      <Sparkles size={13} color="#22d3ee" />
                      <span>View Landing Page</span>
                    </button>
                    <span className="matchBadge" style={{ color: '#2ed573', borderColor: '#2ed573', background: 'rgba(46, 213, 115, 0.12)' }}>
                      ● Session Verified
                    </span>
                  </div>
                </div>
              </div>

              {/* DASHBOARD MODULE TABS */}
              <div className="dashboardTabs">
                <button
                  type="button"
                  className={`dashTab ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  <Sparkles size={15} />
                  <span>Overview / Hero</span>
                </button>

                <button
                  type="button"
                  className={`dashTab ${activeTab === 'matchmaker' ? 'active' : ''}`}
                  onClick={() => setActiveTab('matchmaker')}
                >
                  <Bot size={15} />
                  <span>AI Matchmaker</span>
                </button>

                <button
                  type="button"
                  className={`dashTab ${activeTab === 'friends' ? 'active' : ''}`}
                  onClick={() => setActiveTab('friends')}
                >
                  <Users size={15} />
                  <span>Friends & Network</span>
                </button>

                <button
                  type="button"
                  className={`dashTab ${activeTab === 'squads' ? 'active' : ''}`}
                  onClick={() => setActiveTab('squads')}
                >
                  <Shield size={15} />
                  <span>My Squads</span>
                </button>

                <button
                  type="button"
                  className={`dashTab ${activeTab === 'news' ? 'active' : ''}`}
                  onClick={() => setActiveTab('news')}
                >
                  <Newspaper size={15} />
                  <span>Esports & News</span>
                </button>

                {isAdmin && (
                  <button
                    type="button"
                    className={`dashTab ${activeTab === 'admin' ? 'active' : ''}`}
                    onClick={() => setActiveTab('admin')}
                    style={{
                      color: activeTab === 'admin' ? '#ffffff' : '#ff6363'
                    }}
                  >
                    <ShieldAlert size={15} />
                    <span>Admin Hub</span>
                  </button>
                )}
              </div>

              {/* TAB CONTENT */}
              {activeTab === 'matchmaker' && (
                <div style={{ marginTop: '20px' }}>
                  <MatchmakerDashboard />
                </div>
              )}

              {activeTab === 'friends' && (
                <div style={{ marginTop: '20px' }}>
                  <FriendsHub onOpenChat={handleOpenChat} />
                </div>
              )}

              {activeTab === 'squads' && (
                <div style={{ marginTop: '20px' }}>
                  <SquadsHub onOpenSquadChat={handleOpenChat} />
                </div>
              )}

              {activeTab === 'news' && (
                <div style={{ marginTop: '20px' }}>
                  <NewsHub />
                </div>
              )}

              {activeTab === 'admin' && isAdmin && (
                <div style={{ marginTop: '20px' }}>
                  <AdminDashboard />
                </div>
              )}

              {/* PLATFORM SUMMARY BOX */}
              <div className="glassCard" style={{
                marginTop: '56px',
                padding: '20px 24px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '14px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', textAlign: 'left' }}>
                  <CheckCircle2 color="#2ed573" size={22} />
                  <div>
                    <strong style={{ color: '#ffffff', fontSize: '14px', fontWeight: 600, display: 'block', fontFamily: "'Space Grotesk', sans-serif" }}>
                      Squad Sync Command Platform • All Systems Operational
                    </strong>
                    <span style={{ color: '#94a3b8', fontSize: '13px' }}>
                      AI Gamer DNA™, competitive matchmaking, player conduct moderation, and real-time WebSocket comms.
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span className="matchBadge">
                    Esports News
                  </span>
                  <span className="matchBadge">
                    Moderation SLA
                  </span>
                  <span className="matchBadge">
                    WebSockets
                  </span>
                </div>
              </div>
            </div>
          )}
        </main>
      )}

      {/* REAL-TIME CHAT DOCK (SRS 4.8) */}
      <ChatDrawer
        activeChatTarget={activeChatTarget}
        onCloseTarget={() => setActiveChatTarget(null)}
      />

      {/* FOOTER */}
      {isAuthenticated && activeTab !== 'overview' && (
        <footer style={{
          padding: '24px 40px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          textAlign: 'center',
          color: '#64748b',
          fontSize: '12px',
          fontFamily: "'Outfit', sans-serif",
          letterSpacing: '0.2px'
        }}>
          v1.0.0 &nbsp;|&nbsp; IEEE 830 Specification &nbsp;|&nbsp; Squad Sync AI Platform
        </footer>
      )}
    </div>
  );
}

export default App;
