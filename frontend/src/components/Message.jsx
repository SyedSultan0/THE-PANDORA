import React, { useState } from 'react';
import { Bot, User, Volume2, VolumeX, Copy, Check, Lightbulb, Sparkles, Terminal } from 'lucide-react';

export default function Message({ message, onSpeakToggle, isSpeaking = false }) {
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [showHints, setShowHints] = useState(false);
  const isAi = message.sender === 'ai' || message.sender === 'interviewer';

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Helper to format text and detect code blocks ```code```
  const renderFormattedText = (rawText) => {
    if (!rawText) return null;
    const parts = rawText.split(/(```[\s\S]*?```)/g);

    return parts.map((part, idx) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.slice(3, -3).trim().split('\n');
        const language = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
        const codeBody = language ? lines.slice(1).join('\n') : lines.join('\n');

        return (
          <div key={idx} className="code-block" style={{ margin: '14px 0' }}>
            <div className="code-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Terminal size={14} color="var(--primary-light)" />
                <span>{language || 'code snippet'}</span>
              </div>
              <button
                type="button"
                onClick={() => copyToClipboard(codeBody, idx)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: copiedIndex === idx ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '0.75rem'
                }}
              >
                {copiedIndex === idx ? <Check size={14} /> : <Copy size={14} />}
                {copiedIndex === idx ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="code-content">
              <code>{codeBody}</code>
            </pre>
          </div>
        );
      }

      // Format bold text **text** and linebreaks
      const lineParagraphs = part.split('\n\n').map((para, pIdx) => {
        const boldParsed = para.split(/(\*\*.*?\*\*)/g).map((chunk, cIdx) => {
          if (chunk.startsWith('**') && chunk.endsWith('**')) {
            return (
              <strong key={cIdx} style={{ color: '#fff', fontWeight: 700 }}>
                {chunk.slice(2, -2)}
              </strong>
            );
          }
          if (chunk.startsWith('`') && chunk.endsWith('`')) {
            return (
              <code
                key={cIdx}
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--primary-light)',
                  fontSize: '0.88em'
                }}
              >
                {chunk.slice(1, -1)}
              </code>
            );
          }
          return chunk;
        });

        return (
          <p key={pIdx} style={{ marginBottom: pIdx < part.split('\n\n').length - 1 ? '12px' : 0, lineHeight: 1.65 }}>
            {boldParsed}
          </p>
        );
      });

      return <React.Fragment key={idx}>{lineParagraphs}</React.Fragment>;
    });
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        gap: '16px',
        marginBottom: '24px',
        flexDirection: isAi ? 'row' : 'row-reverse',
        alignItems: 'flex-start'
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: '42px',
          height: '42px',
          borderRadius: '14px',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: isAi ? 'var(--gradient-brand)' : 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
          boxShadow: isAi ? '0 0 16px var(--primary-glow)' : '0 0 16px rgba(6, 182, 212, 0.4)',
          color: '#fff'
        }}
      >
        {isAi ? <Bot size={22} /> : <User size={22} />}
      </div>

      {/* Message Bubble Container */}
      <div
        style={{
          maxWidth: '82%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isAi ? 'flex-start' : 'flex-end'
        }}
      >
        {/* Speaker Name, Role, & Audio toggle */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '6px',
            padding: '0 4px'
          }}
        >
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>
            {isAi ? message.speakerName || 'AI Interviewer' : 'You (Candidate)'}
          </span>

          {isAi && (
            <span className="badge badge-primary" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
              {message.speakerRole || 'Technical Evaluator'}
            </span>
          )}

          {message.topic && (
            <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
              {message.topic}
            </span>
          )}

          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {message.timestamp || 'Just now'}
          </span>

          {isAi && onSpeakToggle && (
            <button
              type="button"
              onClick={() => onSpeakToggle(message.text)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                color: isSpeaking ? 'var(--primary-light)' : 'var(--text-secondary)',
                cursor: 'pointer',
                padding: '3px 6px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.72rem'
              }}
              title={isSpeaking ? 'Stop voice readout' : 'Read aloud with AI Voice'}
            >
              {isSpeaking ? <VolumeX size={13} /> : <Volume2 size={13} />}
              <span>{isSpeaking ? 'Mute' : 'Voice'}</span>
            </button>
          )}
        </div>

        {/* Message Body Glass Card */}
        <div
          className="glass-card"
          style={{
            padding: '18px 22px',
            borderRadius: isAi ? '4px 20px 20px 20px' : '20px 4px 20px 20px',
            backgroundColor: isAi ? 'rgba(22, 30, 49, 0.85)' : 'rgba(15, 23, 42, 0.92)',
            border: isAi ? '1px solid rgba(99, 102, 241, 0.25)' : '1px solid rgba(6, 182, 212, 0.25)',
            boxShadow: isAi ? 'var(--shadow-md)' : '0 8px 24px -4px rgba(6, 182, 212, 0.15)',
            color: '#e2e8f0',
            fontSize: '0.96rem'
          }}
        >
          {renderFormattedText(message.text)}

          {/* Optional Hints Dropdown for AI Questions */}
          {isAi && message.hints && message.hints.length > 0 && (
            <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                onClick={() => setShowHints(!showHints)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-amber)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.8rem',
                  fontWeight: 600
                }}
              >
                <Lightbulb size={15} />
                <span>{showHints ? 'Hide Question Hints' : 'Need a Hint / Guidance?'}</span>
              </button>

              {showHints && (
                <div
                  className="animate-fade-in"
                  style={{
                    marginTop: '10px',
                    padding: '10px 14px',
                    background: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.2)',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    color: '#fde68a'
                  }}
                >
                  <ul style={{ paddingLeft: '18px', margin: 0 }}>
                    {message.hints.map((hint, hIdx) => (
                      <li key={hIdx} style={{ marginBottom: '4px' }}>
                        {hint}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
