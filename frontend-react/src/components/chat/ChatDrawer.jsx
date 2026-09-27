import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { chatApi } from '../../api/chatApi';
import { friendsApi } from '../../api/friendsApi';
import { squadsApi } from '../../api/squadsApi';
import {
  MessageSquare,
  X,
  Send,
  Users,
  Shield,
  Minimize2,
  Loader2
} from 'lucide-react';

function ChatDrawer({ activeChatTarget, onCloseTarget }) {
  const { user, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [channelType, setChannelType] = useState('direct'); // 'direct' | 'team'
  const [activeTarget, setActiveTarget] = useState(null); // { type, id, name, role, isOnline }

  // Channel Lists
  const [friendsList, setFriendsList] = useState([]);
  const [squadsList, setSquadsList] = useState([]);

  // Messages & Socket
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connecting' | 'connected' | 'disconnected'
  const [unreadCount, setUnreadCount] = useState(0);

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Auto-scroll to bottom when messages update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle external open request (e.g. from FriendCard or SquadCard)
  useEffect(() => {
    if (activeChatTarget) {
      setIsOpen(true);
      setChannelType(activeChatTarget.type);
      setActiveTarget(activeChatTarget);
      if (onCloseTarget) onCloseTarget();
    }
  }, [activeChatTarget, onCloseTarget]);

  // Fetch Friends and Squads for channel list
  const loadChannels = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const [fRes, sRes] = await Promise.all([
        friendsApi.getFriends().catch(() => ({ data: [] })),
        squadsApi.getMySquads().catch(() => ({ data: [] }))
      ]);

      const friends = fRes?.data?.data || fRes?.data || (Array.isArray(fRes) ? fRes : []);
      const squads = sRes?.data?.data || sRes?.data || (Array.isArray(sRes) ? sRes : []);

      setFriendsList(friends);
      setSquadsList(squads);

      // Default select first available friend or squad if none selected
      if (!activeTarget) {
        if (friends.length > 0) {
          setActiveTarget({
            type: 'direct',
            id: friends[0].user_id,
            name: friends[0].gamer_tag || friends[0].username,
            role: friends[0].primary_role || 'Flex',
            isOnline: friends[0].is_online !== false
          });
        } else if (squads.length > 0) {
          setActiveTarget({
            type: 'team',
            id: squads[0].id,
            name: squads[0].name,
            role: squads[0].game,
            isOnline: true
          });
          setChannelType('team');
        }
      }
    } catch (err) {
      console.warn('Failed to load chat channels:', err);
    }
  }, [isAuthenticated, activeTarget]);

  useEffect(() => {
    if (isAuthenticated) {
      loadChannels();
    }
  }, [isAuthenticated, loadChannels]);

  // Fetch chat history whenever activeTarget changes
  const loadHistory = useCallback(async () => {
    if (!activeTarget?.id) return;
    try {
      let res;
      if (activeTarget.type === 'direct') {
        res = await chatApi.getDirectHistory(activeTarget.id, 50);
      } else {
        res = await chatApi.getTeamHistory(activeTarget.id, 50);
      }
      const history = res?.data?.data || res?.data || (Array.isArray(res) ? res : []);
      setMessages(history);
    } catch (err) {
      console.warn('Failed to load chat history:', err);
    }
  }, [activeTarget]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Establish Authenticated WebSocket Connection
  useEffect(() => {
    if (!isAuthenticated) return;

    const token = localStorage.getItem('squadsync_token');
    if (!token) return;

    const wsUrl = `ws://127.0.0.1:8000/api/v1/chat/ws?token=${token}`;
    setConnectionStatus('connecting');

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);

        if (payload.type === 'pong') return;

        if (payload.type === 'new_direct_message') {
          const newMsg = payload.data;
          // Check if this message belongs to the currently active target
          if (
            activeTarget?.type === 'direct' &&
            (newMsg.sender_id === activeTarget.id || newMsg.recipient_id === activeTarget.id)
          ) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === newMsg.id)) return prev;
              return [...prev, newMsg];
            });
          } else {
            setUnreadCount((prev) => prev + 1);
          }
        } else if (payload.type === 'new_team_message') {
          const newMsg = payload.data;
          if (activeTarget?.type === 'team' && activeTarget.id === newMsg.team_id) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === newMsg.id)) return prev;
              return [...prev, newMsg];
            });
          } else {
            setUnreadCount((prev) => prev + 1);
          }
        } else if (payload.type === 'user_typing') {
          if (activeTarget?.type === 'direct' && activeTarget.id === payload.sender_id) {
            setIsTyping(true);
            if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
            typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 2000);
          }
        }
      } catch (err) {
        console.error('WebSocket message parsing error:', err);
      }
    };

    ws.onerror = (err) => {
      console.warn('Chat WebSocket connection error:', err);
      setConnectionStatus('disconnected');
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
    };

    // Ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [isAuthenticated, activeTarget]);

  // Send Message Handler
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputText.trim() || !activeTarget) return;

    const content = inputText.trim();
    setInputText('');

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      if (activeTarget.type === 'direct') {
        socketRef.current.send(
          JSON.stringify({
            type: 'direct_message',
            recipient_id: activeTarget.id,
            content
          })
        );
      } else {
        socketRef.current.send(
          JSON.stringify({
            type: 'team_message',
            team_id: activeTarget.id,
            content
          })
        );
      }
    } else {
      // Fallback message display if WS is reconnecting
      const optimisticMsg = {
        id: 'opt-' + Date.now(),
        sender_id: user?.id,
        sender_username: user?.gamer_tag || user?.username,
        content,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, optimisticMsg]);
    }
  };

  // Broadcast typing indicator
  const handleInputChange = (e) => {
    setInputText(e.target.value);
    if (
      activeTarget?.type === 'direct' &&
      socketRef.current &&
      socketRef.current.readyState === WebSocket.OPEN
    ) {
      socketRef.current.send(
        JSON.stringify({
          type: 'typing',
          recipient_id: activeTarget.id
        })
      );
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  if (!isAuthenticated) return null;

  return (
    <>
      {/* FLOATING CHAT BUTTON (WHEN MINIMIZED) */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => {
            setIsOpen(true);
            setUnreadCount(0);
          }}
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            width: '50px',
            height: '50px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #22d3ee, #8b5cf6)',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 25px rgba(34, 211, 238, 0.4), 0 0 20px rgba(139, 92, 246, 0.3)',
            cursor: 'pointer',
            zIndex: 999,
            transition: 'all var(--transition-fast)',
          }}
          title="Open SquadSync Tactical Chat"
        >
          <MessageSquare size={22} color="#ffffff" />
          {unreadCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                background: 'var(--rose)',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: 'var(--radius-pills)',
                fontFamily: 'var(--font-geistmono)',
                boxShadow: '0 0 10px rgba(244, 63, 94, 0.6)'
              }}
            >
              {unreadCount}
            </span>
          )}
        </button>
      )}

      {/* CHAT DOCK (WHEN OPEN) */}
      {isOpen && (
        <div
          className="glassCard"
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            width: '390px',
            maxWidth: 'calc(100vw - 32px)',
            height: '530px',
            maxHeight: 'calc(100vh - 48px)',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: '24px',
            zIndex: 1000,
            boxShadow: '0 24px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(34, 211, 238, 0.15)',
            border: '1px solid var(--border)',
            background: 'rgba(13, 19, 33, 0.96)',
            backdropFilter: 'blur(20px)',
            overflow: 'hidden',
            padding: 0
          }}
        >
          {/* HEADER */}
          <div
            style={{
              padding: '14px 18px',
              borderBottom: '1px solid var(--border)',
              background: 'rgba(255, 255, 255, 0.02)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.2))',
                  border: '1px solid var(--border)',
                  color: '#ffffff',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontFamily: "'Space Grotesk', sans-serif",
                }}
              >
                {(activeTarget?.name || 'S').substring(0, 2).toUpperCase()}
              </div>
              <div style={{ textAlign: 'left' }}>
                <strong style={{ color: '#ffffff', fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', fontFamily: "'Space Grotesk', sans-serif" }}>
                  {activeTarget?.name || 'Tactical Chat'}
                  <span
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      background: connectionStatus === 'connected' ? '#10b981' : 'var(--cyan)',
                      boxShadow: connectionStatus === 'connected' ? '0 0 8px rgba(16, 185, 129, 0.8)' : 'none',
                      display: 'inline-block',
                    }}
                    title={`WebSocket: ${connectionStatus}`}
                  />
                </strong>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-geistmono)' }}>
                  {activeTarget?.type === 'team' ? 'Squad Channel' : `Role: ${activeTarget?.role || 'Teammate'}`}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text2)', cursor: 'pointer', padding: '4px' }}
                title="Minimize Chat"
              >
                <Minimize2 size={16} />
              </button>
            </div>
          </div>

          {/* CHANNEL TYPE TABS */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid var(--border)',
              background: 'rgba(0, 0, 0, 0.25)',
            }}
          >
            <button
              type="button"
              onClick={() => setChannelType('direct')}
              style={{
                flex: 1,
                padding: '10px 14px',
                fontSize: '12px',
                fontWeight: channelType === 'direct' ? 600 : 500,
                border: 'none',
                background: channelType === 'direct' ? 'rgba(34, 211, 238, 0.1)' : 'transparent',
                color: channelType === 'direct' ? 'var(--cyan)' : 'var(--text2)',
                borderBottom: channelType === 'direct' ? '2px solid var(--cyan)' : '2px solid transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                fontFamily: "'Space Grotesk', sans-serif",
                transition: 'all var(--transition-fast)'
              }}
            >
              <Users size={14} />
              <span>Friends ({friendsList.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setChannelType('team')}
              style={{
                flex: 1,
                padding: '10px 14px',
                fontSize: '12px',
                fontWeight: channelType === 'team' ? 600 : 500,
                border: 'none',
                background: channelType === 'team' ? 'rgba(34, 211, 238, 0.1)' : 'transparent',
                color: channelType === 'team' ? 'var(--cyan)' : 'var(--text2)',
                borderBottom: channelType === 'team' ? '2px solid var(--cyan)' : '2px solid transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                fontFamily: "'Space Grotesk', sans-serif",
                transition: 'all var(--transition-fast)'
              }}
            >
              <Shield size={14} />
              <span>Squads ({squadsList.length})</span>
            </button>
          </div>

          {/* CHANNEL SELECTOR CHIPS */}
          <div
            style={{
              padding: '8px 14px',
              display: 'flex',
              gap: '6px',
              overflowX: 'auto',
              borderBottom: '1px solid var(--border)',
              background: 'rgba(0, 0, 0, 0.15)',
            }}
          >
            {channelType === 'direct' ? (
              friendsList.length === 0 ? (
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-geistmono)' }}>No friends added yet</span>
              ) : (
                friendsList.map((f) => {
                  const isSelected = activeTarget?.id === f.user_id;
                  return (
                    <button
                      key={f.user_id}
                      type="button"
                      onClick={() =>
                        setActiveTarget({
                          type: 'direct',
                          id: f.user_id,
                          name: f.gamer_tag || f.username,
                          role: f.primary_role || 'Flex',
                          isOnline: f.is_online !== false,
                        })
                      }
                      style={{
                        padding: '4px 10px',
                        borderRadius: 'var(--radius-pills)',
                        fontSize: '11px',
                        fontWeight: isSelected ? 600 : 500,
                        whiteSpace: 'nowrap',
                        border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                        background: isSelected ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                        color: isSelected ? '#ffffff' : 'var(--text2)',
                        boxShadow: isSelected ? '0 0 10px rgba(34, 211, 238, 0.2)' : 'none',
                        cursor: 'pointer',
                        fontFamily: 'var(--font-geistmono)',
                      }}
                    >
                      {f.gamer_tag || f.username}
                    </button>
                  );
                })
              )
            ) : squadsList.length === 0 ? (
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-geistmono)' }}>No squads created yet</span>
            ) : (
              squadsList.map((s) => {
                const isSelected = activeTarget?.id === s.id;
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() =>
                      setActiveTarget({
                        type: 'team',
                        id: s.id,
                        name: s.name,
                        role: s.game,
                        isOnline: true,
                      })
                    }
                    style={{
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-pills)',
                      fontSize: '11px',
                      fontWeight: isSelected ? 600 : 500,
                      whiteSpace: 'nowrap',
                      border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                      background: isSelected ? 'rgba(34, 211, 238, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                      color: isSelected ? '#ffffff' : 'var(--text2)',
                      boxShadow: isSelected ? '0 0 10px rgba(34, 211, 238, 0.2)' : 'none',
                      cursor: 'pointer',
                      fontFamily: 'var(--font-geistmono)',
                    }}
                  >
                    {s.name}
                  </button>
                );
              })
            )}
          </div>

          {/* MESSAGE STREAM */}
          <div
            style={{
              flex: 1,
              padding: '16px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              background: 'rgba(6, 9, 17, 0.6)',
            }}
          >
            {messages.length === 0 ? (
              <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                <MessageSquare size={32} color="var(--cyan)" style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p style={{ margin: '0 0 4px 0', color: 'var(--text2)' }}>Start coordination with {activeTarget?.name || 'this channel'}.</p>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-geistmono)' }}>
                  Sub-second WebSocket telemetry active.
                </span>
              </div>
            ) : (
              messages.map((m) => {
                const isMe = m.sender_id === user?.id;
                return (
                  <div
                    key={m.id}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: isMe ? 'flex-end' : 'flex-start',
                    }}
                  >
                    {!isMe && (
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px', fontFamily: 'var(--font-geistmono)' }}>
                        {m.sender_username || 'Teammate'}
                      </span>
                    )}

                    <div
                      style={{
                        maxWidth: '85%',
                        padding: '10px 14px',
                        borderRadius: isMe ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                        background: isMe ? 'linear-gradient(135deg, rgba(34, 211, 238, 0.25), rgba(139, 92, 246, 0.25))' : 'rgba(255, 255, 255, 0.05)',
                        color: '#ffffff',
                        fontWeight: 400,
                        fontSize: '13px',
                        lineHeight: 1.4,
                        wordBreak: 'break-word',
                        border: isMe ? '1px solid rgba(34, 211, 238, 0.4)' : '1px solid var(--border)',
                        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.3)',
                      }}
                    >
                      {m.content}
                    </div>

                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '3px', fontFamily: 'var(--font-geistmono)' }}>
                      {formatTime(m.created_at)}
                    </span>
                  </div>
                );
              })
            )}

            {isTyping && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--cyan)' }}>
                <Loader2 size={12} className="animate-spin" />
                <span>{activeTarget?.name || 'Teammate'} is typing...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* INPUT FORM */}
          <form
            onSubmit={handleSendMessage}
            style={{
              padding: '12px 14px',
              borderTop: '1px solid var(--border)',
              background: 'rgba(13, 19, 33, 0.98)',
              display: 'flex',
              gap: '8px',
            }}
          >
            <input
              type="text"
              value={inputText}
              onChange={handleInputChange}
              placeholder={`Message ${activeTarget?.name || 'channel'}...`}
              style={{
                flex: 1,
                fontSize: '13px',
                padding: '10px 14px',
                borderRadius: 'var(--radius-buttons)',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border)',
                color: '#ffffff',
                outline: 'none',
              }}
            />

            <button
              type="submit"
              disabled={!inputText.trim()}
              className="primaryBtn"
              style={{
                padding: '10px 16px',
                borderRadius: 'var(--radius-buttons)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default ChatDrawer;
