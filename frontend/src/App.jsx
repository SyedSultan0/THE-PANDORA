import { useRef, useState } from "react";
import SessionStart from "./components/SessionStart.jsx";
import InterviewSection from "./components/InterviewSection.jsx";
import CompletionCard from "./components/CompletionCard.jsx";
import { startInterview, submitAnswer } from "./services/api.js";

/** Generate a unique session id for a new interview. */
function generateSessionId() {
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function App() {
  const [phase, setPhase] = useState("start"); // 'start' | 'interview' | 'done'
  const [candidate, setCandidate] = useState({
    name: "",
    jobRole: "",
    yearsExperience: "",
    education: "",
  });
  const [sessionId, setSessionId] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState(null);
  const busyRef = useRef(false);

  const startInterviewFlow = async () => {
    if (busyRef.current) return; // Prevent duplicate submissions.
    busyRef.current = true;
    setError("");
    setIsThinking(true);

    const newSessionId = generateSessionId();
    try {
      const data = await startInterview(newSessionId, candidate);
      // Only transition to the interview screen after a successful response.
      setSessionId(newSessionId);
      setQuestion(data.reply);
      setAnswer("");
      setPhase("interview");
    } catch (err) {
      // Stay on the start screen so the user can retry.
      setError(err.message || "Unable to start the interview. Please try again.");
    } finally {
      setIsThinking(false);
      busyRef.current = false;
    }
  };

  const submitAnswerFlow = async () => {
    if (busyRef.current) return; // Prevent duplicate submissions.
    busyRef.current = true;
    setError("");
    setIsThinking(true);

    const submittedAnswer = answer;
    try {
      const data = await submitAnswer(sessionId, submittedAnswer);
      if (data.done) {
        // Completion: stop asking questions and show the real feedback.
        setFeedback(data.feedback);
        setPhase("done");
      } else {
        // The backend reply may be a main question or a follow-up; the
        // backend is the source of truth, so display it as-is.
        setQuestion(data.reply);
        // Only clear the answer after a successful response, so the user
        // can retry without retyping on failure.
        setAnswer("");
      }
    } catch (err) {
      // Stay on the interview screen; the sessionId is preserved so the
      // user can retry the same answer.
      setError(err.message || "Unable to submit your answer. Please try again.");
    } finally {
      setIsThinking(false);
      busyRef.current = false;
    }
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
            onStart={startInterviewFlow}
            isStarting={isThinking}
          />
        )}

        {phase === "interview" && (
          <InterviewSection
            question={question}
            answer={answer}
            onAnswerChange={setAnswer}
            onSubmit={submitAnswerFlow}
            isThinking={isThinking}
          />
        )}

        {phase === "done" && feedback && <CompletionCard feedback={feedback} />}

        {error && <div className="error-banner" role="alert">{error}</div>}
      </main>
    </div>
  );
}