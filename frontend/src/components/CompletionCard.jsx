export default function CompletionCard({ feedback }) {
  return (
    <section className="card completion-card">
      <h2>Interview Complete</h2>
      <p className="summary-text">{feedback.summary}</p>

      <div className="feedback-group">
        <h3>Strengths</h3>
        <ul>
          {feedback.strengths.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="feedback-group">
        <h3>Areas to Improve</h3>
        <ul>
          {feedback.gaps.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="feedback-group">
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