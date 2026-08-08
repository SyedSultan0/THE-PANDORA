import React, { useState } from 'react';
import { INTERVIEW_TRACKS } from '../services/api';
import { Bot, Sparkles, Code2, Layers, Cpu, Award, ChevronRight, CheckCircle2, ShieldCheck, Zap, ArrowRight, User } from 'lucide-react';

export default function Home({ onStartInterview }) {
  const [selectedTrackId, setSelectedTrackId] = useState(INTERVIEW_TRACKS[0].id);
  const [candidateName, setCandidateName] = useState('Alex Taylor');
  const [targetRole, setTargetRole] = useState('Senior Staff Engineer');
  const [experienceLevel, setExperienceLevel] = useState('5-8 Years');

  const selectedTrack = INTERVIEW_TRACKS.find((t) => t.id === selectedTrackId) || INTERVIEW_TRACKS[0];

  const getTrackIcon = (iconName) => {
    switch (iconName) {
      case 'code': return <Code2 size={24} color="var(--primary-light)" />;
      case 'layers': return <Layers size={24} color="var(--accent-cyan)" />;
      case 'bot': return <Cpu size={24} color="var(--secondary)" />;
      case 'award': return <Award size={24} color="var(--accent-amber)" />;
      default: return <Sparkles size={24} color="var(--primary-light)" />;
    }
  };

  const handleStart = (e) => {
    e.preventDefault();
    onStartInterview(selectedTrackId, {
      name: candidateName || 'Candidate',
      targetRole: targetRole || selectedTrack.role,
      experience: experienceLevel
    });
  };

  return (
    <div className="app-container" style={{ padding: '40px 24px 80px 24px' }}>
      {/* Hero Header */}
      <div style={{ textAlign: 'center', maxWidth: '840px', margin: '0 auto 48px auto' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid var(--border-glow)',
            borderRadius: '999px',
            marginBottom: '20px'
          }}
        >
          <Sparkles size={16} color="var(--primary-light)" />
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary-light)' }}>
            Next-Gen Multi-Agent Technical Interview Simulator
          </span>
        </div>

        <h1 style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.15, marginBottom: '18px' }}>
          Ace High-Stakes Tech Interviews with <span className="gradient-text">Adaptive AI Evaluators</span>
        </h1>

        <p style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 auto', maxWidth: '700px' }}>
          Realistic conversational interviews covering concurrency, distributed systems, system design, and leadership. Get instant line-by-line rubric evaluations and competency scores.
        </p>

        {/* Feature Badges */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '24px',
            marginTop: '28px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <Zap size={16} color="var(--accent-cyan)" />
            <span>Real-time Voice & Code Input</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <ShieldCheck size={16} color="var(--accent-emerald)" />
            <span>Standardized Rubric Grading</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#cbd5e1' }}>
            <Bot size={16} color="var(--secondary)" />
            <span>Adaptive Follow-up Probing</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Track Selection + Candidate Setup Card */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '32px', alignItems: 'start' }}>
        {/* Left Column: Track Selection */}
        <div>
          <h3 style={{ fontSize: '1.35rem', marginBottom: '8px', color: '#fff' }}>
            1. Select Your Interview Track
          </h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
            Choose a specialized track tailored with authentic technical question banks.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {INTERVIEW_TRACKS.map((track) => {
              const isSelected = track.id === selectedTrackId;
              return (
                <div
                  key={track.id}
                  onClick={() => setSelectedTrackId(track.id)}
                  className={`glass-card ${isSelected ? 'animate-pulse-glow' : 'glass-card-hover'}`}
                  style={{
                    padding: '20px 22px',
                    cursor: 'pointer',
                    borderRadius: '16px',
                    border: isSelected ? '2px solid var(--primary-light)' : '1px solid var(--border-subtle)',
                    background: isSelected ? 'rgba(30, 41, 67, 0.9)' : 'rgba(15, 23, 42, 0.75)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div
                        style={{
                          width: '46px',
                          height: '46px',
                          borderRadius: '12px',
                          background: 'rgba(255, 255, 255, 0.04)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        {getTrackIcon(track.icon)}
                      </div>
                      <div>
                        <h4 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '2px' }}>{track.title}</h4>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target: {track.role}</span>
                      </div>
                    </div>

                    <span className="badge badge-primary">{track.difficulty}</span>
                  </div>

                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
                    {track.description}
                  </p>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {track.tags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        style={{
                          fontSize: '0.72rem',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: '#94a3b8',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          border: '1px solid rgba(255,255,255,0.05)'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Candidate Info & Curriculum Overview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Candidate Form */}
          <div
            className="glass-card"
            style={{
              padding: '28px',
              borderRadius: '20px',
              border: '1px solid var(--border-glow)',
              background: 'rgba(18, 24, 38, 0.9)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
              <User size={20} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>2. Candidate Profile</h3>
            </div>

            <form onSubmit={handleStart} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Candidate Full Name
                </label>
                <input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="e.g. Alex Johnson"
                  required
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid var(--border-subtle)',
                    color: '#fff',
                    outline: 'none',
                    fontSize: '0.95rem'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Target Role
                  </label>
                  <input
                    type="text"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g. Senior Frontend"
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      background: 'rgba(0, 0, 0, 0.35)',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      outline: 'none',
                      fontSize: '0.95rem'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Experience Level
                  </label>
                  <select
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      background: '#090d16',
                      border: '1px solid var(--border-subtle)',
                      color: '#fff',
                      outline: 'none',
                      fontSize: '0.95rem'
                    }}
                  >
                    <option value="1-3 Years (Junior / Mid)">1-3 Years (Junior / Mid)</option>
                    <option value="4-7 Years (Senior)">4-7 Years (Senior)</option>
                    <option value="8+ Years (Staff / Lead)">8+ Years (Staff / Lead)</option>
                    <option value="12+ Years (Principal / Exec)">12+ Years (Principal / Exec)</option>
                  </select>
                </div>
              </div>

              {/* Selected Track Rubric Preview */}
              <div
                style={{
                  marginTop: '8px',
                  padding: '16px',
                  borderRadius: '12px',
                  background: 'rgba(99, 102, 241, 0.05)',
                  border: '1px solid rgba(99, 102, 241, 0.15)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-light)' }}>
                    Evaluation Rubric Breakdown
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {selectedTrack.initialQuestions.length} Core Modules
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedTrack.rubric.map((r, rIdx) => (
                    <div key={rIdx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                      <span style={{ color: '#cbd5e1' }}>{r.name}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                        {r.weight}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Start CTA Button */}
              <button
                type="submit"
                className="btn btn-primary btn-lg btn-glow"
                style={{ width: '100%', marginTop: '10px' }}
              >
                <span>Launch AI Interview Session</span>
                <ArrowRight size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
