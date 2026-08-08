import { useState } from "react";

export default function InterviewSection({
  question,
  questionNumber,
  answer,
  onAnswerChange,
  onSubmit,
  isThinking,
}) {
  const [answerError, setAnswerError] = useState("");

  const handleChange = (event) => {
    onAnswerChange(event.target.value);
    if (answerError) {
      setAnswerError("");
    }
  };

  const handleSubmit = () => {
    if (!answer.trim()) {
      setAnswerError("Please enter an answer before submitting.");
      return;
    }
    setAnswerError("");
    onSubmit();
  };

  return (
    <section className="card interview-section">
      <div className="progress-area" aria-label="Interview progress">
        <div className="progress-header">
          <span className="progress-label">Question {questionNumber}</span>
        </div>
      </div>

      <div className="question-area" aria-label="Current question">
        <span className="area-label">Current Question</span>
        <p className="question-text">{question}</p>
      </div>

      <div className={`answer-area${answerError ? " has-error" : ""}`}>
        <label htmlFor="answer-input" className="area-label">
          Your Answer
        </label>
        <textarea
          id="answer-input"
          rows="6"
          value={answer}
          onChange={handleChange}
          placeholder="Type your answer here..."
          disabled={isThinking}
          aria-invalid={Boolean(answerError)}
          aria-describedby={answerError ? "answer-input-error" : undefined}
        />
        {answerError && (
          <p className="field-error" id="answer-input-error" role="alert">
            {answerError}
          </p>
        )}
      </div>

      <button
        type="button"
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={isThinking}
      >
        {isThinking ? "Submitting..." : "Submit Answer"}
      </button>

      {isThinking && (
        <p className="thinking" role="status">
          Thinking...
        </p>
      )}
    </section>
  );
}