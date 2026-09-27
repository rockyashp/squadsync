import React, { useState, useEffect } from 'react';
import StepIndicator from './StepIndicator';
import Step1GamerDNA from './Step1GamerDNA';
import Step2SelectGame from './Step2SelectGame';
import Step3SquadMode from './Step3SquadMode';
import Step4AIDraft from './Step4AIDraft';

export default function MatchmakerDashboard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedGame, setSelectedGame] = useState('VALORANT');
  const [isDnaSaved, setIsDnaSaved] = useState(false);

  useEffect(() => {
    const hasDna = localStorage.getItem('squadsync_dna_submitted') === 'true';
    if (hasDna) {
      setIsDnaSaved(true);
      // If user already saved DNA, default to Step 2
      setCurrentStep(2);
    }
  }, []);

  const handleDnaComplete = (profile) => {
    setIsDnaSaved(true);
    setCurrentStep(2);
  };

  const handleGameSelected = (gameId) => {
    setSelectedGame(gameId);
  };

  const handleGameConfirmed = () => {
    setCurrentStep(3);
  };

  const handleSquadModeCreate = () => {
    setCurrentStep(4);
  };

  return (
    <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
      {/* STEP PROGRESS BAR */}
      <StepIndicator
        currentStep={currentStep}
        setStep={setCurrentStep}
        isDnaSaved={isDnaSaved}
      />

      {/* STEP 1: GAMER DNA */}
      {currentStep === 1 && (
        <Step1GamerDNA
          onComplete={handleDnaComplete}
          initialProfile={null}
        />
      )}

      {/* STEP 2: SELECT GAME */}
      {currentStep === 2 && (
        <Step2SelectGame
          selectedGame={selectedGame}
          onSelectGame={handleGameSelected}
          onContinue={handleGameConfirmed}
        />
      )}

      {/* STEP 3: SQUAD MODE */}
      {currentStep === 3 && (
        <Step3SquadMode
          onSelectCreate={handleSquadModeCreate}
          selectedGame={selectedGame}
        />
      )}

      {/* STEP 4: AI MATCHMAKING & SQUAD BUILDER */}
      {currentStep === 4 && (
        <Step4AIDraft
          selectedGame={selectedGame}
        />
      )}
    </div>
  );
}
