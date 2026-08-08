import React from 'react';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

export default function ProgressBar({ currentStep = 1, totalSteps = 4, progressPercent = 25, stageName = 'Technical Assessment', timeLeft = '24:30' }) {
  const percent = Math.min(100, Math.max(0, progressPercent));

  return (
    <div className="glass-card" style={{ padding: '16px 20px', borderRadius: '16px', width: '100%' }}>
      {/* Header Info */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-primary">
            Question {currentStep} of {totalSteps}
          </span>
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>
            {stageName}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {timeLeft && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              <Clock size={15} color="var(--primary-light)" />
              <span style={{ fontFamily: 'var(--font-mono)' }}>{timeLeft}</span>
            </div>
          )}
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-light)' }}>
            {percent}% Completed
          </span>
        </div>
      </div>

      {/* Progress Bar Line */}
      <div
        style={{
          width: '100%',
          height: '8px',
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          borderRadius: '999px',
          overflow: 'hidden',
          position: 'relative'
        }}
      >
        <div
          style={{
            width: `${percent}%`,
            height: '100%',
            background: 'var(--gradient-brand)',
            borderRadius: '999px',
            transition: 'width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
            boxShadow: '0 0 12px var(--primary-glow)'
          }}
        />
      </div>

      {/* Step Dots Indicators */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', padding: '0 4px' }}>
        {Array.from({ length: totalSteps }).map((_, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.75rem',
                color: isCurrent ? '#fff' : isCompleted ? 'var(--accent-emerald)' : 'var(--text-muted)',
                fontWeight: isCurrent ? 700 : 500
              }}
            >
              {isCompleted ? (
                <CheckCircle2 size={14} color="var(--accent-emerald)" />
              ) : isCurrent ? (
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary)',
                    boxShadow: '0 0 8px var(--primary-light)'
                  }}
                />
              ) : (
                <Circle size={12} color="rgba(255,255,255,0.2)" />
              )}
              <span>Part {stepNumber}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
