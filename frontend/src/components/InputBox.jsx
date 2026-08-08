import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff, Code2, Sparkles, CornerDownLeft, RefreshCw } from 'lucide-react';

export default function InputBox({ onSendMessage, disabled = false, placeholder = 'Type your technical answer, system design, or explanation...' }) {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Web Speech API for voice input if supported by browser
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
      };

      recognition.onerror = () => {
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 260)}px`;
    }
  }, [text]);

  const toggleRecording = () => {
    if (!speechSupported || !recognitionRef.current) return;
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error('Speech recognition error:', err);
      }
    }
  };

  const insertCodeTemplate = () => {
    const codeSample = '```javascript\n// Write your algorithm or component implementation here\nfunction solution() {\n  \n}\n```\n';
    setText((prev) => (prev ? `${prev}\n\n${codeSample}` : codeSample));
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const insertStarterChip = (prefix) => {
    setText((prev) => (prev ? `${prev} ${prefix} ` : `${prefix} `));
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!text.trim() || disabled) return;

    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  return (
    <div
      className="glass-card"
      style={{
        padding: '16px 20px',
        borderRadius: '20px',
        border: '1px solid var(--border-glow)',
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        boxShadow: '0 12px 35px -8px rgba(0, 0, 0, 0.7)'
      }}
    >
      {/* Quick Starter Chips */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          overflowX: 'auto',
          paddingBottom: '10px',
          marginBottom: '10px',
          borderBottom: '1px solid var(--border-subtle)'
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Sparkles size={13} color="var(--primary-light)" />
          Quick Starters:
        </span>
        {[
          'From an architectural standpoint...',
          'Let’s break down the trade-offs...',
          'Step 1: Data Model & Ingestion...',
          'For edge cases and failure modes...'
        ].map((starter, sIdx) => (
          <button
            key={sIdx}
            type="button"
            onClick={() => insertStarterChip(starter)}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '999px',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              padding: '3px 10px',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease'
            }}
          >
            {starter}
          </button>
        ))}
      </div>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={3}
        style={{
          width: '100%',
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: '#f8fafc',
          fontFamily: 'var(--font-sans)',
          fontSize: '0.975rem',
          lineHeight: 1.6,
          resize: 'none',
          minHeight: '75px',
          maxHeight: '260px'
        }}
      />

      {/* Controls Footer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '12px',
          paddingTop: '8px',
          borderTop: '1px solid var(--border-subtle)'
        }}
      >
        {/* Left Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {speechSupported && (
            <button
              type="button"
              onClick={toggleRecording}
              disabled={disabled}
              className={isRecording ? 'btn btn-glow' : 'btn btn-secondary btn-sm'}
              style={{
                background: isRecording ? 'var(--accent-rose)' : 'rgba(255, 255, 255, 0.05)',
                color: '#fff',
                borderColor: isRecording ? 'var(--accent-rose)' : 'var(--border-subtle)',
                boxShadow: isRecording ? '0 0 16px rgba(244, 63, 94, 0.6)' : 'none'
              }}
              title={isRecording ? 'Stop voice recording' : 'Record voice with Speech-to-Text'}
            >
              {isRecording ? <MicOff size={15} /> : <Mic size={15} />}
              <span>{isRecording ? 'Listening...' : 'Voice Dictate'}</span>
            </button>
          )}

          <button
            type="button"
            onClick={insertCodeTemplate}
            disabled={disabled}
            className="btn btn-secondary btn-sm"
            title="Insert Code Snippet block"
          >
            <Code2 size={15} color="var(--accent-cyan)" />
            <span>Insert Code</span>
          </button>
        </div>

        {/* Word count & Submit */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {wordCount} words {text.length > 0 && `• ${text.length} chars`}
          </span>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || !text.trim()}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.88rem' }}
          >
            {disabled ? (
              <>
                <RefreshCw size={15} className="animate-spin" />
                <span>Evaluating Answer...</span>
              </>
            ) : (
              <>
                <span>Submit Answer</span>
                <Send size={15} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
