import React, { useRef, useEffect, useState } from 'react';
import Message from './Message';
import { Bot, Sparkles, AlertCircle } from 'lucide-react';

export default function ChatWindow({ messages = [], isThinking = false, thinkingStatus = 'Analyzing response against rubric...' }) {
  const scrollRef = useRef(null);
  const [speakingText, setSpeakingText] = useState(null);

  // Auto scroll to bottom when new message arrives or thinking state changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isThinking]);

  // Voice synthesis readout using Web Speech API
  const handleSpeakToggle = (text) => {
    if (!window.speechSynthesis) return;

    if (speakingText === text) {
      window.speechSynthesis.cancel();
      setSpeakingText(null);
    } else {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text.replace(/```[\s\S]*?```/g, 'Code block omitted.'));
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      utterance.onend = () => setSpeakingText(null);
      utterance.onerror = () => setSpeakingText(null);
      window.speechSynthesis.speak(utterance);
      setSpeakingText(text);
    }
  };

  return (
    <div
      ref={scrollRef}
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        position: 'relative'
      }}
    >
      {/* Session Milestone Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px auto',
          padding: '6px 18px',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '999px',
          color: 'var(--primary-light)',
          fontSize: '0.78rem',
          fontWeight: 600,
          gap: '8px'
        }}
      >
        <Sparkles size={14} />
        <span>Live Adaptive Session • Rubric Evaluation Active</span>
      </div>

      {/* Message List */}
      {messages.map((msg, index) => (
        <Message
          key={msg.id || index}
          message={msg}
          onSpeakToggle={handleSpeakToggle}
          isSpeaking={speakingText === msg.text}
        />
      ))}

      {/* AI Thinking / Evaluating Animation */}
      {isThinking && (
        <div
          className="animate-fade-in"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            padding: '16px 20px',
            background: 'rgba(22, 30, 49, 0.9)',
            border: '1px solid var(--border-glow)',
            borderRadius: '16px',
            maxWidth: '480px',
            boxShadow: 'var(--shadow-glow)',
            marginBottom: '16px'
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'var(--gradient-brand)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff'
            }}
          >
            <Bot size={20} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>AI Interviewer is thinking</span>
              <div style={{ display: 'flex', gap: '4px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary-light)', animation: 'pulseGlow 1s infinite' }} />
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--secondary)', animation: 'pulseGlow 1s infinite 0.2s' }} />
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-cyan)', animation: 'pulseGlow 1s infinite 0.4s' }} />
              </div>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
              {thinkingStatus}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
