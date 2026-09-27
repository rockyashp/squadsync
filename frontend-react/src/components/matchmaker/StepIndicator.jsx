import React from 'react';
import { Check, Dna, Gamepad2, Users, Bot } from 'lucide-react';

const steps = [
  { id: 1, label: 'Gamer DNA™', icon: Dna },
  { id: 2, label: 'Select Game', icon: Gamepad2 },
  { id: 3, label: 'Squad Mode', icon: Users },
  { id: 4, label: 'AI Matchmaking', icon: Bot },
];

export default function StepIndicator({ currentStep, setStep, isDnaSaved }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '6px',
      background: 'var(--color-ink)',
      border: '1px solid #232528',
      borderRadius: 'var(--radius-buttons)',
      padding: '4px',
      boxShadow: 'var(--shadow-key)',
      marginBottom: '24px',
      flexWrap: 'wrap'
    }}>
      {steps.map((step) => {
        const Icon = step.icon;
        const isActive = currentStep === step.id;
        const isCompleted = step.id === 1 ? isDnaSaved : currentStep > step.id;

        return (
          <button
            key={step.id}
            type="button"
            onClick={() => setStep(step.id)}
            title={`Step ${step.id}: ${step.label}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '6px',
              border: isActive ? '1px solid #454647' : '1px solid transparent',
              background: isActive ? 'var(--color-graphite)' : 'transparent',
              color: isActive ? '#ffffff' : isCompleted ? 'var(--color-ash)' : 'var(--color-smoke)',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 500,
              fontFamily: 'var(--font-inter)',
              transition: 'all 0.15s ease'
            }}
          >
            {isCompleted ? (
              <Check size={13} color="#4ade80" strokeWidth={2.5} />
            ) : (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '16px',
                height: '16px',
                borderRadius: '4px',
                background: isActive ? 'var(--color-mist)' : 'var(--color-obsidian)',
                border: '1px solid var(--color-slate)',
                color: isActive ? '#040506' : 'var(--color-smoke)',
                fontSize: '10px',
                fontWeight: 600,
                fontFamily: 'var(--font-geistmono)'
              }}>
                {step.id}
              </span>
            )}
            <Icon size={14} style={{ opacity: isActive || isCompleted ? 1 : 0.6 }} />
            <span>{step.id === 1 && isDnaSaved ? 'Gamer DNA™ Saved' : step.label}</span>
          </button>
        );
      })}
    </div>
  );
}
