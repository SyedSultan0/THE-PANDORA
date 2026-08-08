/**
 * Candidate profiles service.
 *
 * Loads the REAL supplied candidate profiles from the organizer's
 * candidate.json dataset. These are exact profiles — the frontend never
 * invents candidate data. The backend uses this data to personalize the
 * interview.
 */
import candidatesData from "../data/candidates.json";

/**
 * The full list of supplied candidate profiles.
 *
 * @type {Array<{member: object, missions: Array, signals: object}>}
 */
export const CANDIDATES = candidatesData.candidates;

/**
 * Return the candidate profile for a given member id.
 *
 * @param {string} id - Member id (e.g. "CAND-001").
 * @returns {object|undefined} The candidate object, or undefined.
 */
export function getCandidateById(id) {
  return CANDIDATES.find((candidate) => candidate.member.id === id);
}

/**
 * Return a compact display label for a candidate.
 *
 * @param {object} candidate - A candidate profile object.
 * @returns {{id: string, name: string, jobRole: string}}
 */
export function toCandidateSummary(candidate) {
  return {
    id: candidate.member.id,
    name: candidate.member.name,
    jobRole: candidate.member.jobRole,
  };
}