import React, { useState } from 'react';
import Home from './pages/Home';
import Interview from './pages/Interview';
import Feedback from './pages/Feedback';
import { startInterviewSession } from './services/api';
import { Sparkles, Bot, ShieldCheck, Home as HomeIcon, Award } from 'lucide-react';

export default function App() {
  const [currentPage, setCurrentPage] = useState('home'); // 'home' | 'interview' | 'feedback'
  const [currentSession, setCurrentSession] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleStartInterview = async (trackId, candidateInfo) => {
    setLoading(true);
    try {
      const session = await startInterviewSession(trackId, candidateInfo);
      setCurrentSession(session);
      setCurrentPage('interview');
    } catch (err) {
      console.error('Failed to start interview:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFinishInterview = (sessionId) => {
    setCurrentPage('feedback');
  };

  const handleReturnHome = () => {
    setCurrentPage('home');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header className="navbar">
        <div className="app-container nav-content">
          {/* Logo & Brand */}
          <div className="brand-logo" onClick={handleReturnHome}>
            <div className="brand-icon">
              <Bot size={20} />
            </div>
            <div>
              <span>Pandora<span style={{ color: 'var(--primary-light)' }}>AI</span></span>
              <span style={{ fontSize: '0.7rem', display: 'block', color: 'var(--text-muted)', fontWeight: 500, letterSpacing: '0.04em', lineHeight: 1 }}>
                INTERVIEW AGENT
              </span>
            </div>
          </div>

          {/* Navigation & Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: '999px',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                color: '#34d399',
                fontSize: '0.78rem',
                fontWeight: 600
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
              <span>Multi-Agent Evaluator Active</span>
            </div>

            {currentPage !== 'home' && (
              <button
                type="button"
                onClick={handleReturnHome}
                className="btn btn-secondary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <HomeIcon size={14} />
                <span>Home</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Page Router */}
      <main style={{ flex: 1 }}>
        {loading ? (
          <div className="app-container" style={{ textAlign: 'center', padding: '120px 24px' }}>
            <div className="animate-spin" style={{ width: '48px', height: '48px', border: '3px solid rgba(99, 102, 241, 0.2)', borderTopColor: 'var(--primary-light)', borderRadius: '50%', margin: '0 auto 20px auto' }} />
            <h3 style={{ color: '#fff' }}>Preparing Adaptive AI Technical Stage...</h3>
            <p style={{ color: 'var(--text-secondary)' }}>Configuring real-time rubric criteria and prompt context.</p>
          </div>
        ) : currentPage === 'home' ? (
          <Home onStartInterview={handleStartInterview} />
        ) : currentPage === 'interview' ? (
          <Interview
            session={currentSession}
            onFinishInterview={handleFinishInterview}
          />
        ) : (
          <Feedback
            sessionId={currentSession?.sessionId || 'sample_session'}
            onRetake={handleReturnHome}
          />
        )}
      </main>

      {/* Minimal Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '20px 0',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
          background: 'rgba(7, 9, 14, 0.9)'
        }}
      >
        <div className="app-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <span>© 2026 Pandora AI Interview Agent • High-Fidelity Technical Simulation</span>
          <div style={{ display: 'flex', gap: '16px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>React 19 + Vite</span>
            <span style={{ color: 'var(--text-secondary)' }}>FastAPI Ready</span>
            <span style={{ color: 'var(--text-secondary)' }}>Rubric Architecture</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
