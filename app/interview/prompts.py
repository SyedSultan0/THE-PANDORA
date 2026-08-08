"""Prompt construction for interview components.

The system prompts and context serialization live here, separate from the
generator/evaluator business logic, so the prompts can later be refined and
documented without touching the components.
"""

import json

from app.context.models import InterviewContext
from app.interview.models import EvaluationResult, GeneratedQuestion

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


EVALUATION_SYSTEM_PROMPT = """\
You are a fair and rigorous technical interviewer evaluating a candidate's answer.

Evaluate the candidate's ACTUAL answer against the technical requirements implied
by the question that was asked.

Rules:
- Distinguish correct, partially correct, and incorrect answers.
- Do NOT require exact wording; recognize technically valid alternative explanations.
- Do NOT penalize the candidate for omitting information the question never asked for.
- Use the candidate's role, experience, and curriculum context only as background;
  evaluate primarily against the question itself.
- Do NOT invent facts about the candidate.
- Identify concrete strengths and meaningful gaps in the answer.
- Provide concise reasoning for the score.
- Return ONLY a single JSON object with the exact shape described below.
"""

EVALUATION_OUTPUT_INSTRUCTIONS = """\
Return ONLY a valid JSON object with this exact shape:

{
  "score": <integer 0-10>,
  "correctness": "<CORRECT|PARTIAL|INCORRECT>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "gaps": ["<gap 1>", "<gap 2>", ...],
  "reasoning": "<concise explanation of the score>",
  "confidence": "<LOW|MEDIUM|HIGH or null>"
}

Score scale (0-10):
  0   = no meaningful answer
  1-3 = very weak
  4-5 = partial/basic understanding
  6-7 = good understanding
  8-9 = strong understanding
  10  = excellent/deep understanding

The "reasoning" field is required and must be non-empty.
Do not include any text outside the JSON object.
"""

FOLLOW_UP_SYSTEM_PROMPT = """\
You are a realistic technical interviewer conducting a one-on-one technical interview.

You must ask exactly ONE follow-up question based on the candidate's previous answer.

Use the original question, the candidate's answer, and the evaluation to decide what to ask:
- If the answer was partial or had gaps, probe the identified gap or ask for clarification.
- If the answer was incorrect, clarify foundational understanding.
- If the answer was strong, deepen the topic or test practical understanding.
- Consider the candidate's experience and the current difficulty when appropriate.

Rules:
- Do NOT repeat the original question.
- Stay on the same topic; do NOT switch to an unrelated topic.
- Do NOT give away the answer or provide coaching before asking the question.
- Do NOT invent facts about the candidate.
- Return ONLY a single JSON object with the exact shape described below.
"""

FOLLOW_UP_OUTPUT_INSTRUCTIONS = """\
Return ONLY a valid JSON object with this exact shape:

{
  "question": "the follow-up question text",
  "curriculum_day": <integer day number from the supplied context, or null>,
  "topic": "<short topic label matching the context, or null>",
  "difficulty": "<easy|medium|hard, or null>"
}

The "question" field is required and must be non-empty.
Do not include any text outside the JSON object.
"""


def build_evaluation_prompt(
    question: GeneratedQuestion,
    answer: str,
    context: InterviewContext,
) -> str:
    """Build the full evaluation prompt for the LLM.

    Args:
        question: The question the candidate answered.
        answer: The candidate's answer text.
        context: The normalized interview context.

    Returns:
        A single string prompt combining the system instructions, the
        question, the answer, relevant context, and output requirements.
    """
    sections = [
        EVALUATION_SYSTEM_PROMPT,
        "\n# Question Asked\n" + _question_section(question),
        "\n# Candidate Answer\n" + answer.strip(),
        "\n# Candidate Context\n" + _candidate_section(context),
        "\n# Mission History\n" + _missions_section(context),
        "\n# Curriculum Days\n" + _curriculum_days_section(context),
        "\n# Output Format\n" + EVALUATION_OUTPUT_INSTRUCTIONS,
    ]
    return "\n".join(sections)


def build_follow_up_prompt(
    question: GeneratedQuestion,
    answer: str,
    evaluation: EvaluationResult,
    context: InterviewContext,
) -> str:
    """Build the full follow-up question prompt for the LLM.

    Args:
        question: The original question the candidate answered.
        answer: The candidate's answer text.
        evaluation: The evaluation of the candidate's answer.
        context: The normalized interview context.

    Returns:
        A single string prompt combining the system instructions, the
        original question, the answer, the evaluation, relevant context,
        and output requirements.
    """
    sections = [
        FOLLOW_UP_SYSTEM_PROMPT,
        "\n# Original Question\n" + _question_section(question),
        "\n# Candidate Answer\n" + answer.strip(),
        "\n# Evaluation\n" + _evaluation_section(evaluation),
        "\n# Candidate Context\n" + _candidate_section(context),
        "\n# Relevant Curriculum\n" + _curriculum_days_section(context),
        "\n# Interview State\n" + _interview_state_section(context),
        "\n# Output Format\n" + FOLLOW_UP_OUTPUT_INSTRUCTIONS,
    ]
    return "\n".join(sections)


def _evaluation_section(evaluation: EvaluationResult) -> str:
    lines = [
        f"- Score: {evaluation.score}/10",
        f"- Correctness: {evaluation.correctness}",
        f"- Strengths: {json.dumps(evaluation.strengths)}",
        f"- Gaps: {json.dumps(evaluation.gaps)}",
        f"- Reasoning: {evaluation.reasoning}",
    ]
    if evaluation.confidence is not None:
        lines.append(f"- Confidence: {evaluation.confidence}")
    return "\n".join(lines)


def _question_section(question: GeneratedQuestion) -> str:
    lines = [f"- Question: {question.question}"]
    if question.curriculum_day is not None:
        lines.append(f"- Curriculum day: {question.curriculum_day}")
    if question.topic is not None:
        lines.append(f"- Topic: {question.topic}")
    if question.difficulty is not None:
        lines.append(f"- Difficulty: {question.difficulty}")
    return "\n".join(lines)


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