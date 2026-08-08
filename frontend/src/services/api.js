/**
 * Frontend API service for the AI Interview Agent.
 *
 * All HTTP communication with the FastAPI backend lives here so React
 * components stay free of fetch/API logic.
 *
 * The service converts network failures, HTTP errors, and malformed
 * responses into clean, user-facing error messages. Raw stack traces,
 * API keys, and internal backend details are never surfaced.
 */

// Default to same-origin so the Vite dev proxy (see vite.config.js) handles
// /api and /health locally. Override with VITE_API_BASE_URL for a different
// backend origin (e.g. a deployed environment).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const GENERIC_ERROR = "The interview service is unavailable. Please try again.";
const NETWORK_ERROR = "Unable to reach the interview service. Please check your connection and try again.";

/**
 * Start a new interview session.
 *
 * The candidate object is the REAL supplied candidate profile from
 * candidate.json — the frontend does not invent candidate fields.
 *
 * @param {string} sessionId - Client-generated unique session id.
 * @param {object} candidate - The real candidate profile object.
 * @returns {Promise<{reply: string, done: boolean, feedback: object|null}>}
 */
export async function startInterview(sessionId, candidate) {
  const data = await postInterview({
    sessionId,
    candidate,
  });
  return validateInterviewResponse(data);
}

/**
 * Submit a candidate answer for an existing session.
 *
 * @param {string} sessionId - The session id returned at start.
 * @param {string} message - The candidate's answer text.
 * @returns {Promise<{reply: string, done: boolean, feedback: object|null}>}
 */
export async function submitAnswer(sessionId, message) {
  const data = await postInterview({ sessionId, message });
  return validateInterviewResponse(data);
}

/**
 * Check backend health.
 *
 * @returns {Promise<boolean>} True when the backend reports healthy.
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      return false;
    }
    const data = await response.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}

/**
 * POST a payload to /api/interview with full error handling.
 */
async function postInterview(payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/interview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    // Network failure, DNS failure, connection refused, CORS, etc.
    throw new Error(NETWORK_ERROR);
  }

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  try {
    return await response.json();
  } catch {
    // 200 with a non-JSON body is an unexpected response format.
    throw new Error(GENERIC_ERROR);
  }
}

/**
 * Extract a safe, user-facing error message from a failed response.
 */
async function extractErrorMessage(response) {
  let detail = "";
  try {
    const data = await response.json();
    detail = data?.detail;
  } catch {
    // Non-JSON error body; fall through to status-based messaging.
  }

  // Prefer a clean backend-provided message when available.
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  switch (response.status) {
    case 400:
      return "The request could not be processed. Please check your input and try again.";
    case 404:
      return "The interview session was not found. Please start a new interview.";
    case 409:
      return "An interview with this session already exists. Please start a new interview.";
    case 422:
      return "The request is missing required information. Please check your input and try again.";
    case 500:
    default:
      return GENERIC_ERROR;
  }
}

/**
 * Validate and normalize the interview response.
 *
 * Guarantees the object the UI consumes has the expected shape, and throws
 * a controlled error instead of letting malformed data crash the React app.
 *
 * @param {unknown} data - Raw parsed response body.
 * @returns {{reply: string, done: boolean, feedback: object|null}}
 */
export function validateInterviewResponse(data) {
  if (!data || typeof data !== "object") {
    throw new Error("The interview service returned an invalid response.");
  }

  if (typeof data.reply !== "string" || !data.reply.trim()) {
    throw new Error("The interview service returned no question.");
  }

  if (typeof data.done !== "boolean") {
    throw new Error("The interview service returned an invalid completion state.");
  }

  let feedback = null;
  if (data.done === true) {
    feedback = normalizeFeedback(data.feedback);
  }

  return {
    reply: data.reply,
    done: data.done,
    feedback,
  };
}

/**
 * Normalize a feedback object to the shape CompletionCard expects.
 *
 * Missing or malformed optional lists degrade to empty arrays rather than
 * crashing the completion screen.
 *
 * @param {unknown} feedback - Raw feedback value from the response.
 * @returns {object}
 */
function normalizeFeedback(feedback) {
  if (!feedback || typeof feedback !== "object") {
    return { summary: "Interview complete.", strengths: [], gaps: [], next: [] };
  }

  const summary =
    typeof feedback.summary === "string" && feedback.summary.trim()
      ? feedback.summary
      : "Interview complete.";

  return {
    summary,
    strengths: toSafeStringArray(feedback.strengths),
    gaps: toSafeStringArray(feedback.gaps),
    next: toSafeStringArray(feedback.next),
  };
}

/**
 * Return a string array from an unknown value, dropping non-string entries.
 */
function toSafeStringArray(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item) => typeof item === "string");
}