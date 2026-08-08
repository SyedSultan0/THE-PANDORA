import { useState } from "react";
import SessionStart from "./components/SessionStart.jsx";
import InterviewSection from "./components/InterviewSection.jsx";
import CompletionCard from "./components/CompletionCard.jsx";

/** Mock interview questions used to prove the UI flow before API wiring. */
const MOCK_QUESTIONS = [
  "Tell me about your experience building data pipelines.",
  "Explain how vector embeddings are generated.",
  "What is a vector database and when would you use one?",
  "How would you design a retrieval system for a chat assistant?",
  "Describe a time you optimized a slow query.",
  "What are the trade-offs between RAG and fine-tuning?",
  "How do you ensure quality in a production AI system?",
  "Walk me through your approach to writing a technical spec.",
];

export default function App() {
  const [phase, setPhase] = useState("start"); // 'start' | 'interview' | 'done'
  const [candidate, setCandidate] = useState({ name: "", jobRole: "", yearsExperience: "" });
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState(null);

  const startInterview = () => {
    if (!candidate.name.trim() || !candidate.jobRole.trim()) {
      setError("Please provide your name and job role to begin.");
      return;
    }
    setError("");
    setIsThinking(true);
    // Simulate a brief load before entering the interview screen.
    setTimeout(() => {
      setQuestionIndex(0);
      setAnswer("");
      setIsThinking(false);
      setPhase("interview");
    }, 600);
  };

  const submitAnswer = () => {
    if (!answer.trim()) {
      setError("Please enter an answer before submitting.");
      return;
    }
    setError("");
    setAnswer("");
    setIsThinking(true);

    // Simulate a mock "next turn" transition.
    setTimeout(() => {
      setIsThinking(false);
      if (questionIndex + 1 >= MOCK_QUESTIONS.length) {
        setFeedback({
          summary: "Great work! Here is a summary of your interview performance.",
          strengths: ["Strong technical depth", "Clear communication"],
          gaps: ["Could deepen system design discussion"],
          next: ["Review vector database fundamentals", "Practice end-to-end architecture"],
        });
        setPhase("done");
      } else {
        setQuestionIndex((index) => index + 1);
      }
    }, 600);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Interview Agent</h1>
        <p className="app-subtitle">Technical interview practice assistant</p>
      </header>

      <main className="app-main">
        {phase === "start" && (
          <SessionStart
            candidate={candidate}
            onCandidateChange={setCandidate}
            onStart={startInterview}
          />
        )}

        {phase === "interview" && (
          <InterviewSection
            question={MOCK_QUESTIONS[questionIndex]}
            questionNumber={questionIndex + 1}
            totalQuestions={MOCK_QUESTIONS.length}
            answer={answer}
            onAnswerChange={setAnswer}
            onSubmit={submitAnswer}
            isThinking={isThinking}
          />
        )}

        {phase === "done" && feedback && <CompletionCard feedback={feedback} />}

        {error && <div className="error-banner" role="alert">{error}</div>}
      </main>
    </div>
  );
}