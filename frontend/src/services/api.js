/**
 * AI Interview Agent API Service
 * Handles communication with the FastAPI backend (/api/interview/*)
 * with robust intelligent fallback logic for seamless standalone preview.
 */

const API_BASE = '/api';

// Curated Interview Tracks & Real Curriculum Data
export const INTERVIEW_TRACKS = [
  {
    id: 'frontend-react',
    title: 'Frontend / React Specialist',
    role: 'Senior Frontend Engineer',
    icon: 'code',
    difficulty: 'Senior',
    estimatedTime: '25-30 mins',
    description: 'Master React 19, state management, concurrent rendering, Web Vitals, and modern CSS architecture.',
    tags: ['React', 'TypeScript', 'Performance', 'DOM / Event Loop', 'State Architecture'],
    rubric: [
      { name: 'Core JavaScript & React Mastery', weight: 30 },
      { name: 'Component Architecture & State', weight: 25 },
      { name: 'Web Performance & CWV', weight: 20 },
      { name: 'System Design & Tradeoffs', weight: 15 },
      { name: 'Communication & Clarity', weight: 10 }
    ],
    initialQuestions: [
      {
        id: 'q1',
        topic: 'React Concurrency & Rendering',
        difficulty: 'Senior',
        question: "Could you explain how React 18+'s Concurrent Features (such as `useTransition` and `useDeferredValue`) work under the hood with the Fiber reconciler? In what real-world scenario would you choose `useTransition` over standard debounce or throttle?",
        hints: [
          'Mention yielding to the main thread and urgent vs. transition updates.',
          'Consider user perception vs CPU-bound heavy component subtrees.'
        ],
        idealAnswerPoints: [
          'Transitions mark state updates as non-urgent, allowing React to interrupt rendering for user input.',
          'Debounce delays the update execution; useTransition executes immediately in background and stays responsive.',
          'Fiber lanes assign priority levels so high-priority events (typing, clicks) interrupt background tree re-renders.'
        ]
      },
      {
        id: 'q2',
        topic: 'State Architecture & Performance',
        difficulty: 'Senior',
        question: "When architecting a large-scale dashboard receiving 500+ WebSocket message updates per second, how would you design the frontend state pipeline in React to prevent UI frame drops and unnecessary DOM reconciliations?",
        hints: [
          'Think about batching, ref vs state buffers, off-screen canvas/virtualization, and selective subscription selectors.'
        ],
        idealAnswerPoints: [
          'Buffer streaming updates in a ref or Web Worker and flush to state at requestAnimationFrame / 60fps cadence.',
          'Use atomic state libraries (Zustand/Jotai) with fine-grained selectors to isolate rerendering to single cells.',
          'Leverage DOM virtualization (react-window/tanstack-virtual) and CSS content-visibility for offscreen rows.'
        ]
      },
      {
        id: 'q3',
        topic: 'Web Vitals & Core Optimization',
        difficulty: 'Senior',
        question: "Imagine your application's Interaction to Next Paint (INP) is scoring in the 'Poor' category (>500ms) on a data grid filter. Walk me through your step-by-step diagnostic process and remediation strategy.",
        hints: [
          'Think about Chrome DevTools Performance panel, Long Animation Frames (LoAF) API, and main-thread breakdown.'
        ],
        idealAnswerPoints: [
          'Profile with Performance panel and LoAF API to identify input delay, processing time, and presentation delay.',
          'Decompose heavy synchronous filtering into chunks using scheduler.yield() or Web Workers.',
          'Optimize CSS selector complexity and avoid forced synchronous layout recalcs during keydown events.'
        ]
      }
    ]
  },
  {
    id: 'fullstack-python',
    title: 'Fullstack & Python (FastAPI / Node)',
    role: 'Staff Fullstack Engineer',
    icon: 'layers',
    difficulty: 'Lead / Staff',
    estimatedTime: '30-40 mins',
    description: 'Async Python, FastAPI dependency injection, distributed caching, PostgreSQL indexing, and microservices.',
    tags: ['Python 3.12', 'FastAPI', 'PostgreSQL', 'Redis', 'AsyncIO', 'Docker'],
    rubric: [
      { name: 'AsyncIO & Concurrency Internals', weight: 30 },
      { name: 'API Design & Idempotency', weight: 25 },
      { name: 'Database Optimization & Transactions', weight: 25 },
      { name: 'Distributed Systems & Reliability', weight: 20 }
    ],
    initialQuestions: [
      {
        id: 'q1',
        topic: 'Python Concurrency & AsyncIO',
        difficulty: 'Staff',
        question: "In Python 3.12, how does AsyncIO manage cooperative multitasking vs threads vs multiprocessing under the GIL? If a FastAPI endpoint executes CPU-intensive image resizing inside an `async def` route without `run_in_executor`, what happens to all other concurrent HTTP connections?",
        hints: [
          'Remember that `async def` without yielding blocks the single event loop thread entirely.'
        ],
        idealAnswerPoints: [
          'AsyncIO runs on a single OS thread using an event loop (epoll/kqueue); blocking calls starve all coroutines.',
          'CPU-bound tasks in `async def` freeze event loop dispatching, stalling health checks and incoming requests.',
          'Fix with `asyncio.to_thread` or a multiprocessing ProcessPoolExecutor to bypass GIL and thread locks.'
        ]
      },
      {
        id: 'q2',
        topic: 'Distributed Caching & Concurrency',
        difficulty: 'Staff',
        question: "How do you protect your backend services from Cache Stampede (Thundering Herd problem) when a high-traffic cache key with expensive SQL computation expires simultaneously across 10,000 active instances?",
        hints: ['Consider probabilistic early expiration (XFetch), mutex locks, or single-flight / background refresh.'],
        idealAnswerPoints: [
          'Implement mutex / distributed locking in Redis (Redlock or SETNX) so only 1 worker computes while others wait.',
          'Adopt XFetch (probabilistic early expiration algorithm) to recompute cache before TTL hard expiration.',
          'Serve stale data while background asynchronous cron or worker refreshes cache proactively.'
        ]
      }
    ]
  },
  {
    id: 'ai-system-design',
    title: 'AI Systems & LLM Architecture',
    role: 'Senior AI / LLM Engineer',
    icon: 'bot',
    difficulty: 'Senior',
    estimatedTime: '30-35 mins',
    description: 'Retrieval-Augmented Generation (RAG), vector indexing, multi-agent evaluation, token budgeting, and guardrails.',
    tags: ['RAG', 'Vector DB', 'Prompt Engineering', 'LangChain / Agents', 'Latency Optimization'],
    rubric: [
      { name: 'RAG Pipeline & Chunking Strategy', weight: 30 },
      { name: 'Agentic Workflows & Tool Use', weight: 25 },
      { name: 'Eval & Guardrails', weight: 25 },
      { name: 'Cost, Latency & Token Optimization', weight: 20 }
    ],
    initialQuestions: [
      {
        id: 'q1',
        topic: 'Advanced RAG & Retrieval Optimization',
        difficulty: 'Senior',
        question: "Suppose you are designing an enterprise RAG system over 100,000 PDF documents. Dense vector cosine search produces high false positives on specific numerical codes and jargon. How would you architect a hybrid retrieval and reranking pipeline to achieve 98%+ precision?",
        hints: ['Combine BM25 / sparse lexical search with dense embeddings and cross-encoder rerankers.'],
        idealAnswerPoints: [
          'Use Hybrid Search combining dense embeddings (semantic meaning) and sparse BM25/SPLADE (keyword/code exact match) with Reciprocal Rank Fusion (RRF).',
          'Deploy a cross-encoder Reranker (e.g. Cohere or BGE-Reranker) on top-50 results to score exact context query relevance.',
          'Implement contextual chunking with metadata headers (document title, section summary, table parsing).'
        ]
      }
    ]
  },
  {
    id: 'behavioral-leadership',
    title: 'Engineering Leadership & Behavioral',
    role: 'Engineering Manager / Staff Lead',
    icon: 'award',
    difficulty: 'Staff',
    estimatedTime: '20-25 mins',
    description: 'Conflict resolution, cross-functional alignment, system outages, post-mortems, and mentorship.',
    tags: ['STAR Method', 'Conflict Resolution', 'Post-Mortem', 'Mentorship', 'Roadmap Prioritization'],
    rubric: [
      { name: 'STAR Structure & Clarity', weight: 30 },
      { name: 'Leadership & Conflict Resolution', weight: 30 },
      { name: 'Ownership & Accountability', weight: 25 },
      { name: 'Impact & Business Alignment', weight: 15 }
    ],
    initialQuestions: [
      {
        id: 'q1',
        topic: 'Cross-Functional Technical Disagreement',
        difficulty: 'Staff',
        question: "Tell me about a time you strongly disagreed with a Principal Architect or Product Director on a high-stakes technical decision. How did you navigate the disagreement, what evidence did you present, and what was the ultimate outcome?",
        hints: ['Use the STAR method: Situation, Task, Action, Result. Focus on objective data and collaborative decision-making.'],
        idealAnswerPoints: [
          'Clear STAR structure setting context and stakes.',
          'Focus on data, prototypes, and user metrics rather than personal opinion.',
          'Commitment to team velocity and disagree-and-commit principles with defined rollback triggers.'
        ]
      }
    ]
  }
];

// Helper to simulate network latency
const delay = (ms = 600) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Start a new interview session
 */
export async function startInterviewSession(trackId, candidateInfo) {
  try {
    const res = await fetch(`${API_BASE}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_id: trackId, candidate: candidateInfo })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    console.info('Backend not active, using intelligent standalone simulation.');
  }

  // Standalone simulation fallback
  await delay(800);
  const track = INTERVIEW_TRACKS.find((t) => t.id === trackId) || INTERVIEW_TRACKS[0];
  const firstQ = track.initialQuestions[0];

  const session = {
    sessionId: `ses_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    track,
    candidate: candidateInfo || {
      name: 'Alex Johnson',
      targetRole: track.role,
      experience: '5+ Years'
    },
    status: 'in_progress',
    startTime: new Date().toISOString(),
    currentQuestionIndex: 0,
    totalQuestions: track.initialQuestions.length,
    currentQuestion: firstQ,
    messages: [
      {
        id: 'msg_welcome',
        sender: 'ai',
        speakerName: 'Dr. Evelyn Vance',
        speakerRole: 'Principal AI Interviewer',
        text: `Hello ${candidateInfo?.name || 'there'}! Welcome to your **${track.title}** technical session. I'm Dr. Evelyn Vance, your AI technical evaluator today.\n\nWe'll cover core system fundamentals, architectural tradeoffs, and hands-on problem-solving. Feel free to structure your thoughts, write code snippets, or ask clarifying questions at any point.\n\nLet's jump into our first topic: **${firstQ.topic}**.\n\n${firstQ.question}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        topic: firstQ.topic,
        hints: firstQ.hints
      }
    ],
    evaluations: []
  };

  localStorage.setItem(`interview_session_${session.sessionId}`, JSON.stringify(session));
  return session;
}

/**
 * Submit candidate answer / chat message to AI Interviewer
 */
export async function sendInterviewMessage(sessionId, text, currentQuestionId) {
  try {
    const res = await fetch(`${API_BASE}/interview/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        question_id: currentQuestionId
      })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Proceed to standalone simulation
  }

  await delay(1200);

  // Standalone simulated evaluator & interviewer AI response
  const rawSession = localStorage.getItem(`interview_session_${sessionId}`);
  let session = rawSession ? JSON.parse(rawSession) : null;
  const track = session?.track || INTERVIEW_TRACKS[0];

  // Evaluate candidate answer quality based on keywords, depth, and structure
  const wordCount = text.trim().split(/\s+/).length;
  const hasCode = text.includes('```') || text.includes('function') || text.includes('const') || text.includes('async') || text.includes('def ');
  const hasStructure = text.includes('\n') || text.includes('1.') || text.includes('- ');

  let score = 75;
  if (wordCount > 60) score += 10;
  if (wordCount > 120) score += 8;
  if (hasCode || hasStructure) score += 7;
  score = Math.min(score, 98);

  const evaluation = {
    questionId: currentQuestionId || `q_${Date.now()}`,
    questionText: session?.currentQuestion?.question || 'Technical Assessment',
    candidateAnswer: text,
    score,
    strengths: [
      'Good articulation of architectural tradeoffs and real-world failure modes.',
      'Demonstrated solid theoretical grounding on execution boundaries and event loop behavior.',
      wordCount > 80 ? 'Comprehensive explanation with structured, clear technical reasoning.' : 'Concise and direct response.'
    ],
    improvementAreas: [
      'Could cite specific metric instrumentation (e.g. Profiler Traces, p99 latency SLAs).',
      'Consider outlining potential edge-cases during high concurrent spikes or race conditions.'
    ],
    evaluatorNotes: `Candidate achieved ${score}/100. Strong grasp of technical mechanics.`
  };

  const nextIndex = (session?.currentQuestionIndex || 0) + 1;
  const isFinished = nextIndex >= (track.initialQuestions.length || 3);
  let nextQuestion = null;
  let aiReplyText = '';

  if (!isFinished && track.initialQuestions[nextIndex]) {
    nextQuestion = track.initialQuestions[nextIndex];
    aiReplyText = `Great insights on that topic! You demonstrated a sharp grasp of the underlying execution semantics.\n\nNow, let's pivot to **${nextQuestion.topic}** (${nextQuestion.difficulty} level):\n\n${nextQuestion.question}`;
  } else {
    aiReplyText = `Outstanding job! You have completed all core technical modules for the **${track.title}** assessment.\n\nI have generated your comprehensive post-interview scorecard, competency rubric breakdown, and actionable learning recommendations. Click **"View Feedback & Scorecard"** below to review your detailed report!`;
  }

  const aiMessage = {
    id: `msg_ai_${Date.now()}`,
    sender: 'ai',
    speakerName: 'Dr. Evelyn Vance',
    speakerRole: 'Principal AI Interviewer',
    text: aiReplyText,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    topic: nextQuestion ? nextQuestion.topic : 'Assessment Complete',
    hints: nextQuestion ? nextQuestion.hints : []
  };

  if (session) {
    session.currentQuestionIndex = nextIndex;
    session.currentQuestion = nextQuestion;
    session.status = isFinished ? 'completed' : 'in_progress';
    session.evaluations.push(evaluation);
    session.messages.push(aiMessage);
    localStorage.setItem(`interview_session_${sessionId}`, JSON.stringify(session));
  }

  return {
    aiResponse: aiMessage,
    evaluation,
    isFinished,
    nextQuestion,
    progress: Math.round(((nextIndex) / (track.initialQuestions.length || 3)) * 100)
  };
}

/**
 * Fetch full scorecard and feedback for a completed session
 */
export async function getSessionFeedback(sessionId) {
  try {
    const res = await fetch(`${API_BASE}/interview/feedback/${sessionId}`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Proceed to standalone
  }

  await delay(600);
  const raw = localStorage.getItem(`interview_session_${sessionId}`);
  let session = raw ? JSON.parse(raw) : null;

  if (!session) {
    // Return a rich sample report if loaded directly
    const defaultTrack = INTERVIEW_TRACKS[0];
    return generateMockFeedbackReport('sample_session', defaultTrack, {
      name: 'Sarah Chen',
      targetRole: 'Staff Frontend Architect',
      experience: '7+ Years'
    });
  }

  const totalScore = session.evaluations.length > 0
    ? Math.round(session.evaluations.reduce((acc, curr) => acc + curr.score, 0) / session.evaluations.length)
    : 88;

  return {
    sessionId,
    candidate: session.candidate,
    track: session.track,
    overallScore: totalScore,
    hireRecommendation: totalScore >= 85 ? 'Strong Hire' : totalScore >= 70 ? 'Hire' : 'Needs Practice',
    completedAt: new Date().toLocaleString(),
    competencyScores: [
      { category: 'Technical Depth & Mechanics', score: Math.min(100, totalScore + 4), max: 100, grade: 'A' },
      { category: 'System Architecture & Scale', score: Math.min(100, totalScore - 2), max: 100, grade: 'A-' },
      { category: 'Problem Solving & Edge Cases', score: Math.min(100, totalScore + 1), max: 100, grade: 'A' },
      { category: 'Communication & Structuring', score: Math.min(100, totalScore + 6), max: 100, grade: 'A+' },
      { category: 'Code Quality & Cleanliness', score: Math.min(100, totalScore - 3), max: 100, grade: 'B+' }
    ],
    evaluations: session.evaluations.length > 0 ? session.evaluations : [
      {
        questionId: 'q1',
        questionText: 'React Concurrency & Event Loop Internals',
        candidateAnswer: 'Candidate provided in-depth breakdown of fiber lanes, interruptible rendering, and scheduler prioritization.',
        score: 92,
        strengths: ['Clear differentiation between debouncing and concurrent transitions.', 'Good reference to main-thread responsiveness.'],
        improvementAreas: ['Could elaborate on memory overhead of retaining alternate fiber trees.'],
        evaluatorNotes: 'Demonstrated senior-level clarity on React internals.'
      }
    ],
    actionableFeedback: [
      'Practice drawing out state isolation boundaries and profiling with Chrome DevTools LoAF API.',
      'Review Distributed Redlock failure scenarios for high-throughput messaging architectures.',
      'Refine your elevator-pitch summary for architectural tradeoffs to maximize impact during early question rounds.'
    ]
  };
}

function generateMockFeedbackReport(sessionId, track, candidate) {
  return {
    sessionId,
    candidate,
    track,
    overallScore: 91,
    hireRecommendation: 'Strong Hire',
    completedAt: new Date().toLocaleString(),
    competencyScores: [
      { category: 'Technical Depth & Mechanics', score: 94, max: 100, grade: 'A+' },
      { category: 'System Architecture & Scale', score: 89, max: 100, grade: 'A' },
      { category: 'Problem Solving & Edge Cases', score: 92, max: 100, grade: 'A' },
      { category: 'Communication & Structuring', score: 95, max: 100, grade: 'A+' },
      { category: 'Performance & Optimization', score: 86, max: 100, grade: 'B+' }
    ],
    evaluations: [
      {
        questionId: 'q1',
        questionText: "Explain React Concurrent Features (useTransition, useDeferredValue) and Fiber reconciler priority lanes.",
        candidateAnswer: "useTransition marks state updates as non-urgent transitions, yielding control back to the browser main thread so user typing and clicks remain unblocked at 60fps.",
        score: 94,
        strengths: [
          'Accurately described Fiber reconciler priority lanes and cooperative multitasking.',
          'Clearly articulated the distinction between debounce (delayed execution) and transitions (immediate low-priority execution).'
        ],
        improvementAreas: [
          'Could explicitly mention how React handles concurrent update collisions with state setters.'
        ],
        evaluatorNotes: 'Superb grasp of modern frontend performance paradigms.'
      },
      {
        questionId: 'q2',
        questionText: "Architect a 500+ msg/sec WebSocket state pipeline in React without dropping frames.",
        candidateAnswer: "I would buffer incoming WebSocket frames in a mutable ref or Web Worker, then batch flush to state using requestAnimationFrame while isolating row components with Zustand granular selectors.",
        score: 89,
        strengths: [
          'Excellent proposal to decouple transport ingestion rate from UI render cadence with requestAnimationFrame.',
          'Smart utilization of granular atomic selectors to eliminate unnecessary tree reconciliations.'
        ],
        improvementAreas: [
          'Consider mentioning memory footprint constraints under long-lived tab sessions.'
        ],
        evaluatorNotes: 'Very practical, battle-tested system design answer.'
      }
    ],
    actionableFeedback: [
      'Continue demonstrating strong system thinking when discussing performance bottleneck mitigation.',
      'Add quantitative telemetry examples (e.g. reporting web vitals with Google Analytics 4 / Datadog) to elevate staff-level answers.',
      'Explore deep web worker offloading techniques for JSON deserialization on massive payloads.'
    ]
  };
}
