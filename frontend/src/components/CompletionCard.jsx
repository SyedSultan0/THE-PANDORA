export default function CompletionCard({ feedback }) {
  return (
    <section className="card completion-card">
      <div className="completion-header">
        <span className="completion-badge" aria-hidden="true">✓</span>
        <h2>Interview Complete</h2>
      </div>

      <div className="feedback-summary">
        <h3>Summary</h3>
        <p className="summary-text">{feedback.summary}</p>
      </div>

      <div className="feedback-group feedback-strengths">
        <h3>Strengths</h3>
        <ul>
          {feedback.strengths.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="feedback-group feedback-gaps">
        <h3>Areas to Improve</h3>
        <ul>
          {feedback.gaps.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="feedback-group feedback-next">
        <h3>Next Steps</h3>
        <ul>
          {feedback.next.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}