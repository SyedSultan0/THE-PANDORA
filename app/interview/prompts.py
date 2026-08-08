"""Prompt construction for question generation.

The system prompt and context serialization live here, separate from the
QuestionGenerator business logic, so the prompt can later be refined and
documented without touching the generator.
"""

import json

from app.context.models import InterviewContext

QUESTION_SYSTEM_PROMPT = """\
You are a realistic technical interviewer conducting a one-on-one technical interview.

You must ask exactly ONE technical interview question at a time.

Use the supplied candidate and curriculum context to personalize the question:
- Consider the candidate's job role, years of experience, and education.
- Consider the candidate's mission history: passed, failed, and skipped missions.
- Consider the curriculum day/topic that the interviewer has selected.
- Match the question difficulty to the requested difficulty when provided.

Rules:
- Do NOT ask about topics that are not represented in the supplied context.
- Respect the supplied curriculum day/topic; do not invent other topics.
- Do NOT repeat questions that have already been asked.
- Do NOT reveal or hint at the expected answer in the question.
- Do NOT include introductory text, explanations, or preamble.
- Return ONLY a single JSON object with the exact shape described below.
"""

QUESTION_OUTPUT_INSTRUCTIONS = """\
Return ONLY a valid JSON object with this exact shape:

{
  "question": "the interview question text",
  "curriculum_day": <integer day number from the supplied context, or null>,
  "topic": "<short topic label matching the context, or null>",
  "difficulty": "<easy|medium|hard, or null>"
}

The "question" field is required and must be non-empty.
Do not include any text outside the JSON object.
"""


def build_question_prompt(context: InterviewContext) -> str:
    """Build the full prompt for the LLM from an InterviewContext.

    Args:
        context: The normalized interview context.

    Returns:
        A single string prompt combining the system instructions, the
        serialized context, and the structured-output requirements.
    """
    sections = [QUESTION_SYSTEM_PROMPT, "\n# Candidate Context\n", _candidate_section(context)]
    sections.append("\n# Mission History\n" + _missions_section(context))
    sections.append("\n# Curriculum Days\n" + _curriculum_days_section(context))
    sections.append("\n# Interview State\n" + _interview_state_section(context))
    sections.append("\n# Output Format\n" + QUESTION_OUTPUT_INSTRUCTIONS)
    return "\n".join(sections)


def _candidate_section(context: InterviewContext) -> str:
    profile = context.candidate
    lines = [
        f"- Job role: {profile.jobRole}",
        f"- Years of experience: {profile.yearsExperience}",
        f"- Education: {profile.education}",
    ]
    return "\n".join(lines)


def _missions_section(context: InterviewContext) -> str:
    if not context.missions:
        return "- No mission history available."

    lines = []
    for m in context.missions:
        attempts = f", attempts: {m.attempts}" if m.attempts is not None else ""
        lines.append(f"- Day {m.day}: {m.title} — {m.state}{attempts}")
    return "\n".join(lines)


def _curriculum_days_section(context: InterviewContext) -> str:
    if not context.curriculumDays:
        return "- No curriculum days available."

    lines = []
    for info in context.curriculumDays:
        covered = " (already covered)" if info.day in context.interviewState.daysCovered else ""
        lines.append(
            f"- Day {info.day} [module {info.moduleNumber}]: {info.title} "
            f"({info.type}){covered}"
        )
    return "\n".join(lines)


def _interview_state_section(context: InterviewContext) -> str:
    state = context.interviewState
    lines = [
        f"- Current question number: {state.currentQuestionNumber}",
        f"- Days already covered: {json.dumps(state.daysCovered)}",
        f"- Current difficulty: {state.currentDifficulty or 'not specified'}",
        f"- Questions already asked: {json.dumps(state.questionsAsked)}",
    ]
    return "\n".join(lines)