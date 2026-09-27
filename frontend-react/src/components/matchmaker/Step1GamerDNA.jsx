import React, { useState, useEffect } from 'react';
import { matchmakerApi } from '../../api/matchmakerApi';
import { useAuth } from '../../context/AuthContext';
import { Dna, ArrowRight, ShieldCheck, Zap, MessageSquare, Compass, Award } from 'lucide-react';

const QUESTIONS = [
  {
    id: 1,
    title: '1. Enemy team pushes your site aggressively with full utility...',
    options: [
      { text: 'Rotate & Trade Information', role: 'Initiator', lead: 70, agg: 60, comm: 85, sense: 90 },
      { text: 'Swing Immediately for Entry Kill', role: 'Duelist', lead: 50, agg: 95, comm: 60, sense: 70 },
      { text: 'Smoke Chokepoint & Stall', role: 'Controller', lead: 80, agg: 40, comm: 90, sense: 95 },
      { text: 'Anchor Site & Set Defensive Traps', role: 'Sentinel', lead: 75, agg: 30, comm: 75, sense: 98 },
    ],
  },
  {
    id: 2,
    title: '2. Your primary communication style in high-intensity rounds?',
    options: [
      { text: 'IGL / Strategic Directing & Callouts', lead: 95, agg: 65, comm: 95, sense: 90, role: null },
      { text: 'Short, Precise Info Only', lead: 60, agg: 70, comm: 80, sense: 85, role: null },
      { text: 'High Energy & Team Hype', lead: 80, agg: 85, comm: 95, sense: 75, role: null },
    ],
  },
  {
    id: 3,
    title: '3. Team Economy & Loadout Strategy:',
    options: [
      { text: 'Buy loadout for teammate before own weapon', lead: 85, agg: 50, comm: 90, sense: 88, role: null },
      { text: 'Coordinate mutual eco-buy with entire squad', lead: 90, agg: 60, comm: 92, sense: 92, role: null },
      { text: 'Prioritize max loadout for personal impact', lead: 65, agg: 90, comm: 70, sense: 78, role: null },
    ],
  },
  {
    id: 4,
    title: '4. High-Pressure 1v3 Clutch Mindset:',
    options: [
      { text: 'Thrive under pressure & play to win duels', lead: 75, agg: 95, comm: 80, sense: 85, role: null },
      { text: 'Fundamentals first, play methodical angles', lead: 80, agg: 60, comm: 85, sense: 96, role: null },
      { text: 'Save equipment / reset for next round', lead: 85, agg: 40, comm: 80, sense: 90, role: null },
    ],
  },
  {
    id: 5,
    title: '5. Prime Gaming Hours & Commitment:',
    options: [
      { text: 'Evening Squad Grind (6 PM - 10 PM)', lead: 80, agg: 75, comm: 88, sense: 88, role: null },
      { text: 'Late Night Ranked Grind (10 PM - 3 AM)', lead: 70, agg: 85, comm: 85, sense: 90, role: null },
      { text: 'Weekend Tournaments & Scrims', lead: 85, agg: 80, comm: 90, sense: 92, role: null },
    ],
  },
];

export default function Step1GamerDNA({ onComplete, initialProfile }) {
  const { user } = useAuth();
  const [selectedAnswers, setSelectedAnswers] = useState({
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
  });

  const [traits, setTraits] = useState({
    leadership: 85,
    aggression: 72,
    communication: 94,
    game_sense: 91,
    role: 'Initiator',
  });

  const [saving, setSaving] = useState(false);
  const [passScale, setPassScale] = useState(false);

  // Recalculate traits whenever selected answers change
  useEffect(() => {
    let leadSum = 0, aggSum = 0, commSum = 0, senseSum = 0;
    let chosenRole = 'Initiator';

    QUESTIONS.forEach((q) => {
      const optionIdx = selectedAnswers[q.id] || 0;
      const opt = q.options[optionIdx];
      if (opt) {
        leadSum += opt.lead || 75;
        aggSum += opt.agg || 65;
        commSum += opt.comm || 80;
        senseSum += opt.sense || 85;
        if (opt.role) chosenRole = opt.role;
      }
    });

    const count = QUESTIONS.length;
    const finalLead = Math.min(98, Math.max(50, Math.round(leadSum / count)));
    const finalAgg = Math.min(98, Math.max(40, Math.round(aggSum / count)));
    const finalComm = Math.min(98, Math.max(50, Math.round(commSum / count)));
    const finalSense = Math.min(98, Math.max(50, Math.round(senseSum / count)));

    setTraits({
      leadership: finalLead,
      aggression: finalAgg,
      communication: finalComm,
      game_sense: finalSense,
      role: chosenRole,
    });
  }, [selectedAnswers]);

  const handleSelectOption = (questionId, optionIndex) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleContinue = async () => {
    setSaving(true);
    setPassScale(true);
    setTimeout(() => setPassScale(false), 300);

    const payload = {
      leadership: traits.leadership,
      aggression: traits.aggression,
      communication: traits.communication,
      game_sense: traits.game_sense,
      preferred_role: traits.role,
    };

    try {
      await matchmakerApi.generateDNA(payload);
    } catch (err) {
      console.warn('Backend DNA generation completed or using local cache:', err);
    }

    localStorage.setItem('squadsync_dna_submitted', 'true');
    localStorage.setItem('squadsync_dna_profile', JSON.stringify(payload));
    setSaving(false);
    onComplete(payload);
  };

  // Derive dynamic title & synergy tier
  let titlePrefix = 'Master';
  if (traits.aggression > 80) titlePrefix = 'Aggressive';
  else if (traits.communication > 88) titlePrefix = 'Strategic';
  else if (traits.game_sense > 88) titlePrefix = 'Tactical';

  const avgSynergy = (
    (traits.leadership + traits.aggression + traits.communication + traits.game_sense) / 4
  ).toFixed(1);

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', textAlign: 'left' }}>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#ffffff', marginBottom: '6px', letterSpacing: '-0.02em' }}>
          Gamer DNA™ Survey
        </h2>
        <p style={{ color: 'var(--color-smoke)', fontSize: '13px', margin: 0 }}>
          Answer tactical scenarios to calibrate your competitive telemetry and matchmaking heuristics.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(320px, 0.8fr)', gap: '20px' }}>
        {/* QUESTIONS COLUMN */}
        <div className="glassCard" style={{ padding: '24px' }}>
          {QUESTIONS.map((q) => (
            <div key={q.id} style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '10px', fontFamily: "'Space Grotesk', sans-serif" }}>{q.title}</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {q.options.map((opt, optIdx) => {
                  const isSelected = selectedAnswers[q.id] === optIdx;
                  return (
                    <button
                      key={optIdx}
                      type="button"
                      onClick={() => handleSelectOption(q.id, optIdx)}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px 16px',
                        borderRadius: 'var(--radius-md)',
                        border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                        background: isSelected ? 'rgba(34, 211, 238, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                        color: isSelected ? '#ffffff' : 'var(--text2)',
                        boxShadow: isSelected ? '0 0 15px rgba(34, 211, 238, 0.2)' : 'none',
                        cursor: 'pointer',
                        fontSize: '13px',
                        textAlign: 'left',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <span>{opt.text}</span>
                      {opt.role && (
                        <span style={{
                          fontSize: '10px',
                          fontFamily: 'var(--font-geistmono)',
                          padding: '2px 8px',
                          borderRadius: 'var(--radius-pills)',
                          background: isSelected ? 'rgba(34, 211, 238, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                          border: isSelected ? '1px solid var(--cyan)' : '1px solid var(--border)',
                          color: isSelected ? 'var(--cyan)' : 'var(--text2)'
                        }}>
                          {opt.role}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          <button
            type="button"
            className="primaryBtn fullWidth"
            onClick={handleContinue}
            disabled={saving}
            style={{ marginTop: '8px', padding: '12px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <span>{saving ? 'Saving DNA Telemetry...' : 'Confirm DNA & Choose Game'}</span>
            <ArrowRight size={15} />
          </button>
        </div>

        {/* GAMER PASS PREVIEW COLUMN */}
        <div>
          <div
            className="glassCard"
            style={{
              padding: '28px 24px',
              textAlign: 'center',
              transform: passScale ? 'scale(1.02)' : 'scale(1)',
              transition: 'transform 0.25s ease',
            }}
          >
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #22d3ee, #8b5cf6)',
              boxShadow: '0 0 20px rgba(34, 211, 238, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px',
              color: '#ffffff'
            }}>
              <Dna size={24} />
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#ffffff', margin: '0 0 4px 0', fontFamily: "'Space Grotesk', sans-serif" }}>
              {user?.gamer_tag || user?.username || 'Gamer'}
            </h2>
            <p style={{ color: 'var(--text2)', fontWeight: 500, margin: '0 0 12px 0', fontSize: '13px' }}>
              {titlePrefix} {traits.role}
            </p>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: 'var(--radius-pills)',
              background: 'rgba(139, 92, 246, 0.15)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              color: '#c4b5fd',
              fontSize: '11px',
              fontFamily: 'var(--font-geistmono)',
              fontWeight: 500,
              marginBottom: '20px',
            }}>
              <Award size={13} color="var(--violet)" />
              <span>Synergy Rank: S-Tier ({avgSynergy}%)</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
              <div className="trait">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Compass size={13} color="var(--cyan)" /> Leadership
                  </span>
                  <span style={{ color: '#ffffff' }}>{traits.leadership}%</span>
                </div>
                <div style={{ height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${traits.leadership}%`, height: '100%', background: 'linear-gradient(90deg, #22d3ee, #06b6d4)', boxShadow: '0 0 10px rgba(34, 211, 238, 0.5)' }} />
                </div>
              </div>

              <div className="trait">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Zap size={13} color="var(--rose)" /> Aggression
                  </span>
                  <span style={{ color: '#ffffff' }}>{traits.aggression}%</span>
                </div>
                <div style={{ height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${traits.aggression}%`, height: '100%', background: 'linear-gradient(90deg, #f43f5e, #fb7185)', boxShadow: '0 0 10px rgba(244, 63, 94, 0.5)' }} />
                </div>
              </div>

              <div className="trait">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={13} color="var(--violet)" /> Communication
                  </span>
                  <span style={{ color: '#ffffff' }}>{traits.communication}%</span>
                </div>
                <div style={{ height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${traits.communication}%`, height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)', boxShadow: '0 0 10px rgba(139, 92, 246, 0.5)' }} />
                </div>
              </div>

              <div className="trait">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '11px', fontFamily: 'var(--font-geistmono)', color: 'var(--text2)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck size={13} color="var(--emerald)" /> Game Sense
                  </span>
                  <span style={{ color: '#ffffff' }}>{traits.game_sense}%</span>
                </div>
                <div style={{ height: '5px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${traits.game_sense}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #34d399)', boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)' }} />
                </div>
              </div>
            </div>

            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 14px',
              border: '1px solid var(--border)',
              fontSize: '11px',
              fontFamily: 'var(--font-geistmono)',
              color: 'var(--text2)',
              textAlign: 'center',
            }}>
              Neural DNA profile automatically weights synergy algorithms in matchmaking.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
