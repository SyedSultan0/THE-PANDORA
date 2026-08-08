export default function InterviewSection({
  question,
  questionNumber,
  totalQuestions,
  answer,
  onAnswerChange,
  onSubmit,
  isThinking,
}) {
  return (
    <section className="card interview-section">
      <div className="progress-area" aria-label="Interview progress">
        <span className="progress-label">
          Question {questionNumber} of {totalQuestions}
        </span>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
          />
        </div>
      </div>

      <div className="question-area">
        <h2>Current Question</h2>
        <p className="question-text">{question}</p>
      </div>

      <div className="form-field">
        <label htmlFor="answer-input">Your Answer</label>
        <textarea
          id="answer-input"
          rows="6"
          value={answer}
          onChange={(event) => onAnswerChange(event.target.value)}
          placeholder="Type your answer here..."
          disabled={isThinking}
        />
      </div>

      <button
        type="button"
        className="btn btn-primary"
        onClick={onSubmit}
        disabled={isThinking}
      >
        Submit Answer
      </button>

      {isThinking && (
        <p className="thinking" role="status">
          Thinking...
        </p>
      )}
    </section>
  );
}