import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, AlertTriangle, MessageSquare, Award, Sparkles } from 'lucide-react';

export default function FeedbackCard({ evaluation, index = 1 }) {
  const [expanded, setExpanded] = useState(true);

  if (!evaluation) return null;

  const score = evaluation.score || 85;
  const isExcellent = score >= 88;
  const isGood = score >= 75 && score < 88;

  const badgeClass = isExcellent ? 'badge-emerald' : isGood ? 'badge-primary' : 'badge-amber';
  const scoreColor = isExcellent ? 'var(--accent-emerald)' : isGood ? 'var(--primary-light)' : 'var(--accent-amber)';

  return (
    <div
      className="glass-card glass-card-hover"
      style={{
        padding: '22px 24px',
        marginBottom: '20px',
        border: `1px solid ${isExcellent ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'}`,
        background: 'rgba(18, 24, 38, 0.85)'
      }}
    >
      {/* Card Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1rem',
              color: '#fff'
            }}
          >
            Q{index}
          </div>

          <div>
            <h4 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: '4px' }}>
              {evaluation.questionText || `Question Module ${index}`}
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`badge ${badgeClass}`}>
                {isExcellent ? 'Exceeds Expectations' : isGood ? 'Meets Expectations' : 'Needs Practice'}
              </span>
            </div>
          </div>
        </div>

        {/* Score & Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 800, color: scoreColor }}>
              {score}<span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/100</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Rubric Score</div>
          </div>

          <button
            type="button"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      {/* Expandable Breakdown Body */}
      {expanded && (
        <div className="animate-fade-in" style={{ marginTop: '20px', paddingTop: '18px', borderTop: '1px solid var(--border-subtle)' }}>
          {/* Candidate Answer Excerpt */}
          {evaluation.candidateAnswer && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                <MessageSquare size={14} color="var(--primary-light)" />
                <span>Your Submitted Response:</span>
              </div>
              <div
                style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.9rem',
                  color: '#cbd5e1',
                  lineHeight: 1.6,
                  fontFamily: evaluation.candidateAnswer.includes('function') || evaluation.candidateAnswer.includes('```') ? 'var(--font-mono)' : 'var(--font-sans)'
                }}
              >
                {evaluation.candidateAnswer}
              </div>
            </div>
          )}

          {/* Strengths & Improvement 2-Column Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            {/* Key Strengths */}
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.05)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                borderRadius: '12px',
                padding: '14px 16px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '8px' }}>
                <CheckCircle size={15} />
                <span>Key Strengths</span>
              </div>
              <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.85rem', color: '#d1fae5', lineHeight: 1.6 }}>
                {evaluation.strengths && evaluation.strengths.map((str, sIdx) => (
                  <li key={sIdx} style={{ marginBottom: '4px' }}>
                    {str}
                  </li>
                ))}
              </ul>
            </div>

            {/* Areas for Growth */}
            <div
              style={{
                background: 'rgba(245, 158, 11, 0.05)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
                borderRadius: '12px',
                padding: '14px 16px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-amber)', fontWeight: 700, fontSize: '0.85rem', marginBottom: '8px' }}>
                <AlertTriangle size={15} />
                <span>Areas to Elevate</span>
              </div>
              <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.85rem', color: '#fef3c7', lineHeight: 1.6 }}>
                {evaluation.improvementAreas && evaluation.improvementAreas.map((area, aIdx) => (
                  <li key={aIdx} style={{ marginBottom: '4px' }}>
                    {area}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Evaluator Notes */}
          {evaluation.evaluatorNotes && (
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                padding: '12px 14px',
                background: 'rgba(99, 102, 241, 0.06)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                borderRadius: '10px',
                fontSize: '0.85rem',
                color: 'var(--primary-light)'
              }}
            >
              <Award size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>Evaluator Rubric Summary: </strong>
                {evaluation.evaluatorNotes}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
