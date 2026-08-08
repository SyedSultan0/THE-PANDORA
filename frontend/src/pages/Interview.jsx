import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import ProgressBar from '../components/ProgressBar';
import { sendInterviewMessage } from '../services/api';
import { Bot, CheckCircle, Clock, BookOpen, FileText, ChevronRight, Award, AlertCircle } from 'lucide-react';

export default function Interview({ session, onFinishInterview }) {
  const [messages, setMessages] = useState(session?.messages || []);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState('Analyzing answer against rubric...');
  const [currentQuestion, setCurrentQuestion] = useState(session?.currentQuestion);
  const [currentStep, setCurrentStep] = useState(1);
  const [totalSteps, setTotalSteps] = useState(session?.totalQuestions || 3);
  const [progressPercent, setProgressPercent] = useState(25);
  const [scratchpad, setScratchpad] = useState('');
  const [timerSeconds, setTimerSeconds] = useState(1800); // 30 minutes countdown

  // Timer countdown effect
  useEffect(() => {
    const timer = setInterval(() => {
      setTimerSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleSendMessage = async (text) => {
    // Append candidate message immediately
    const userMsg = {
      id: `msg_user_${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);
    setThinkingStatus('Evaluating response depth, complexity, and trade-off considerations...');

    try {
      const response = await sendInterviewMessage(session.sessionId, text, currentQuestion?.id);

      setIsThinking(false);

      if (response?.aiResponse) {
        setMessages((prev) => [...prev, response.aiResponse]);
      }

      if (response?.nextQuestion) {
        setCurrentQuestion(response.nextQuestion);
        setCurrentStep((prev) => prev + 1);
      }

      if (response?.progress) {
        setProgressPercent(response.progress);
      }

      if (response?.isFinished) {
        // Session ended
        setProgressPercent(100);
      }
    } catch (err) {
      console.error('Error in message processing:', err);
      setIsThinking(false);
    }
  };

  const handleFinish = () => {
    if (window.confirm('Are you ready to submit all responses and generate your comprehensive rubric evaluation?')) {
      onFinishInterview(session?.sessionId);
    }
  };

  return (
    <div className="app-container" style={{ padding: '20px 24px 40px 24px', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 70px)' }}>
      {/* Top HUD: Progress Bar & Session Metadata */}
      <div style={{ marginBottom: '16px' }}>
        <ProgressBar
          currentStep={currentStep}
          totalSteps={totalSteps}
          progressPercent={progressPercent}
          stageName={currentQuestion?.topic || session?.track?.title || 'Technical Interview Session'}
          timeLeft={formatTimer(timerSeconds)}
        />
      </div>

      {/* Main Workspace Layout (2 columns: Live Chat + Context HUD) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', flex: 1, minHeight: 0 }}>
        {/* Left Column: Chat History + Answer Input */}
        <div
          className="glass-card"
          style={{
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            borderRadius: '20px',
            border: '1px solid var(--border-glow)',
            backgroundColor: 'rgba(11, 16, 28, 0.85)'
          }}
        >
          {/* Scrollable Chat Area */}
          <ChatWindow
            messages={messages}
            isThinking={isThinking}
            thinkingStatus={thinkingStatus}
          />

          {/* Fixed Input Box at Bottom */}
          <div style={{ padding: '0 16px 16px 16px' }}>
            <InputBox
              onSendMessage={handleSendMessage}
              disabled={isThinking}
              placeholder="State your technical answer, algorithm, or architecture design..."
            />
          </div>
        </div>

        {/* Right Sidebar: Module HUD, Rubric & Scratchpad */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          {/* Active Question Context Card */}
          <div
            className="glass-card"
            style={{
              padding: '18px 20px',
              borderRadius: '16px',
              background: 'rgba(18, 24, 38, 0.85)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <BookOpen size={16} color="var(--primary-light)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
                Active Evaluation Module
              </span>
            </div>

            <h4 style={{ fontSize: '1rem', color: 'var(--primary-light)', marginBottom: '8px' }}>
              {currentQuestion?.topic || 'Core Technical Foundations'}
            </h4>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '12px' }}>
              Focus on concrete trade-offs, internal mechanics, memory/runtime costs, and production reliability.
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              <span className="badge badge-primary">{session?.track?.difficulty || 'Senior'} Level</span>
              <span className="badge badge-cyan">{session?.candidate?.name || 'Candidate'}</span>
            </div>
          </div>

          {/* Rubric Checklist Card */}
          <div
            className="glass-card"
            style={{
              padding: '18px 20px',
              borderRadius: '16px',
              background: 'rgba(18, 24, 38, 0.85)',
              border: '1px solid var(--border-subtle)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Award size={16} color="var(--accent-emerald)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
                Track Competencies
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {session?.track?.rubric?.map((rubricItem, rIdx) => (
                <div key={rIdx} style={{ fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: '#cbd5e1' }}>{rubricItem.name}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-light)' }}>
                      {rubricItem.weight}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '999px' }}>
                    <div
                      style={{
                        width: `${rubricItem.weight * 2.5}%`,
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

          {/* Candidate Scratchpad */}
          <div
            className="glass-card"
            style={{
              padding: '18px 20px',
              borderRadius: '16px',
              background: 'rgba(18, 24, 38, 0.85)',
              border: '1px solid var(--border-subtle)',
              flex: 1,
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <FileText size={16} color="var(--accent-amber)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>
                Candidate Scratchpad
              </span>
            </div>

            <textarea
              value={scratchpad}
              onChange={(e) => setScratchpad(e.target.value)}
              placeholder="Jot down rough notes, pseudocode, or formulas here during the session (private to you)..."
              style={{
                flex: 1,
                minHeight: '90px',
                width: '100%',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '10px',
                color: '#e2e8f0',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                resize: 'none',
                outline: 'none'
              }}
            />
          </div>

          {/* End Interview Button */}
          <button
            type="button"
            onClick={handleFinish}
            className="btn btn-secondary"
            style={{ width: '100%', padding: '12px 16px', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#fff' }}
          >
            <span>Finish & View Scorecard</span>
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
