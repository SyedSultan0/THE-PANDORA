import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import FeedbackCard from '../components/FeedbackCard';
import { getSessionFeedback } from '../services/api';
import { Award, CheckCircle2, ArrowLeft, Download, Share2, Sparkles, TrendingUp, BookOpen, ShieldCheck } from 'lucide-react';

export default function Feedback({ sessionId, onRetake }) {
  const [feedbackData, setFeedbackData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const data = await getSessionFeedback(sessionId);
      setFeedbackData(data);
      setLoading(false);

      // Trigger celebratory confetti if score is high
      if (data?.overallScore >= 80) {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b']
        });
      }
    }
    loadData();
  }, [sessionId]);

  const handleExport = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="app-container" style={{ textAlign: 'center', padding: '100px 24px' }}>
        <div className="animate-spin" style={{ width: '48px', height: '48px', border: '3px solid rgba(99, 102, 241, 0.2)', borderTopColor: 'var(--primary-light)', borderRadius: '50%', margin: '0 auto 20px auto' }} />
        <h3 style={{ color: '#fff' }}>Generating Detailed Competency & Rubric Report...</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Synthesizing evaluator notes and calculating benchmark percentiles.</p>
      </div>
    );
  }

  const { overallScore, hireRecommendation, candidate, track, competencyScores, evaluations, actionableFeedback } = feedbackData;

  const scoreColor = overallScore >= 85 ? 'var(--accent-emerald)' : overallScore >= 70 ? 'var(--primary-light)' : 'var(--accent-amber)';

  return (
    <div className="app-container" style={{ padding: '36px 24px 80px 24px', maxWidth: '1080px' }}>
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
        <button
          type="button"
          onClick={onRetake}
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ArrowLeft size={16} />
          <span>Back to Tracks</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            onClick={handleExport}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Download size={15} />
            <span>Export Report (PDF)</span>
          </button>

          <button
            type="button"
            onClick={onRetake}
            className="btn btn-primary btn-sm"
          >
            <span>Retake Interview</span>
          </button>
        </div>
      </div>

      {/* Hero Scorecard Banner */}
      <div
        className="glass-card"
        style={{
          padding: '32px 36px',
          borderRadius: '24px',
          border: '1px solid var(--border-glow)',
          background: 'radial-gradient(ellipse at top right, rgba(99, 102, 241, 0.15) 0%, rgba(18, 24, 38, 0.95) 70%)',
          marginBottom: '36px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '28px',
          alignItems: 'center'
        }}
      >
        {/* Candidate Info & Hire Verdict */}
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
            <span className="badge badge-emerald">Assessment Completed</span>
            <span className="badge badge-primary">{track?.title || 'Technical Track'}</span>
          </div>

          <h2 style={{ fontSize: '2.2rem', fontWeight: 800, color: '#fff', marginBottom: '8px' }}>
            {candidate?.name || 'Alex Taylor'}
          </h2>

          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Evaluated for <strong>{candidate?.targetRole || track?.role}</strong> • Experience Level: <strong>{candidate?.experience || '5+ Years'}</strong>
          </p>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 18px',
              borderRadius: '12px',
              background: overallScore >= 85 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
              border: `1px solid ${scoreColor}`
            }}
          >
            <ShieldCheck size={20} color={scoreColor} />
            <div>
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', fontWeight: 700 }}>
                Hiring Committee Recommendation
              </span>
              <span style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor }}>
                {hireRecommendation}
              </span>
            </div>
          </div>
        </div>

        {/* Big Circular Score Dial */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div
            style={{
              width: '170px',
              height: '170px',
              borderRadius: '50%',
              background: 'rgba(0, 0, 0, 0.4)',
              border: `4px solid ${scoreColor}`,
              boxShadow: `0 0 35px ${scoreColor}44`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center'
            }}
          >
            <span style={{ fontSize: '3rem', fontWeight: 800, color: '#fff', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
              {overallScore}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '4px' }}>
              Rubric / 100
            </span>
          </div>
        </div>
      </div>

      {/* Competency Pillar Breakdown */}
      <div style={{ marginBottom: '40px' }}>
        <h3 style={{ fontSize: '1.35rem', color: '#fff', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={20} color="var(--accent-cyan)" />
          <span>Competency Matrix & Benchmark Percentiles</span>
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {competencyScores?.map((comp, cIdx) => (
            <div
              key={cIdx}
              className="glass-card"
              style={{
                padding: '18px 20px',
                borderRadius: '16px',
                background: 'rgba(18, 24, 38, 0.85)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Grade</span>
                <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>{comp.grade}</span>
              </div>

              <h4 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '10px' }}>
                {comp.category}
              </h4>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--primary-light)' }}>
                  {comp.score}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/100</span>
              </div>

              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '999px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${comp.score}%`,
                    height: '100%',
                    background: 'var(--gradient-brand)',
                    borderRadius: '999px'
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Question-by-Question Deep Dive */}
      <div style={{ marginBottom: '40px' }}>
        <h3 style={{ fontSize: '1.35rem', color: '#fff', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen size={20} color="var(--primary-light)" />
          <span>Granular Question-by-Question Evaluations</span>
        </h3>

        {evaluations?.map((evalItem, idx) => (
          <FeedbackCard
            key={idx}
            evaluation={evalItem}
            index={idx + 1}
          />
        ))}
      </div>

      {/* Actionable Learning Roadmap */}
      {actionableFeedback && actionableFeedback.length > 0 && (
        <div
          className="glass-card"
          style={{
            padding: '24px 28px',
            borderRadius: '20px',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            background: 'rgba(16, 185, 129, 0.04)'
          }}
        >
          <h3 style={{ fontSize: '1.2rem', color: 'var(--accent-emerald)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} />
            <span>Actionable High-Impact Growth Recommendations</span>
          </h3>

          <ul style={{ paddingLeft: '20px', margin: 0, color: '#e2e8f0', fontSize: '0.925rem', lineHeight: 1.7 }}>
            {actionableFeedback.map((action, aIdx) => (
              <li key={aIdx} style={{ marginBottom: '8px' }}>
                {action}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
