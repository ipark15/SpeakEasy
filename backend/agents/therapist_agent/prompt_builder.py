"""
Builds the ElevenLabs Conversational AI system prompt for the therapist agent.
Called after assessment completes — receives current assessment + history from progress_tracker.
"""

from __future__ import annotations


# ── guardrail topics — checked case-insensitively ─────────────────────────────

_BLOCKED_TOPICS = [
    "diagnosis", "diagnose", "medical advice", "prescription", "prescribe",
    "medication", "medicine", "disorder", "disease", "pathology", "prognosis",
    "dysarthria", "apraxia", "stroke", "neurological", "surgery", "treatment plan",
    "clinical recommendation", "doctor's advice", "cure",
]

_GUARDRAIL_RESPONSE = (
    "That's an important question, but it's outside what I'm able to help with. "
    "I'm a speech practice coach, not a licensed clinician. For medical advice, "
    "diagnoses, or treatment decisions, please consult a licensed speech-language "
    "pathologist or physician. I'm here to support your practice — not replace professional care."
)

_REPORT_REMINDER = (
    "Before we wrap up — your personalized SpeakEasy assessment report is ready. "
    "It includes your scores, a breakdown of every metric we measured, and targeted exercises. "
    "You can download it from the Reports section of the app and bring it to your next appointment "
    "with a speech-language pathologist or physician — it gives them a detailed picture of your speech "
    "patterns that can save a lot of time in a clinical evaluation."
)


# ── score interpretation helpers ──────────────────────────────────────────────

def _score_label(score: float) -> str:
    if score >= 80: return "strong"
    if score >= 65: return "developing"
    if score >= 50: return "needs attention"
    return "a priority focus area"


def _dim_summary(scores: dict) -> str:
    lines = []
    order = ["fluency", "clarity", "rhythm", "prosody", "pronunciation"]
    for dim in order:
        v = scores.get(dim)
        if v is not None:
            lines.append(f"  - {dim.capitalize()}: {v}/100 ({_score_label(v)})")
    return "\n".join(lines) if lines else "  - No dimension scores available."


def _history_summary(history: dict) -> str:
    if not history or history.get("sessions_completed", 0) == 0:
        return "This is the user's first session — no historical data yet."

    n = history["sessions_completed"]
    streak = history.get("current_streak", 0)
    lines = [f"  - Sessions completed: {n}  |  Current practice streak: {streak} day(s)"]

    # Score trend
    trend = history.get("score_trend", [])
    if len(trend) >= 2:
        first = trend[0].get("overall", "?")
        last = trend[-1].get("overall", "?")
        direction = "improving" if isinstance(first, (int, float)) and isinstance(last, (int, float)) and last > first else "fluctuating"
        lines.append(f"  - Overall score trend: {first} → {last} ({direction})")

    # Dimension averages
    dim_avgs = history.get("dimension_averages", {})
    if dim_avgs:
        worst = min(dim_avgs, key=lambda k: dim_avgs[k])
        best = max(dim_avgs, key=lambda k: dim_avgs[k])
        lines.append(f"  - Historically strongest dimension: {best.capitalize()} ({dim_avgs[best]})")
        lines.append(f"  - Historically weakest dimension: {worst.capitalize()} ({dim_avgs[worst]})")

    # Recurring words
    recurring = history.get("recurring_low_confidence_words", [])
    if recurring:
        word_list = ", ".join(f'"{w["word"]}" ({w["avg_confidence"]:.0%} avg, {w["occurrences"]} sessions)' for w in recurring[:5])
        lines.append(f"  - Words consistently unclear across sessions: {word_list}")

    return "\n".join(lines)


def _task_highlights(tasks: list) -> str:
    lines = []
    for t in tasks:
        tid = t.get("task_id", "")
        m = t.get("metrics", {})
        label = {"read_sentence": "Read Aloud", "pataka": "Pa-ta-ka", "free_speech": "Free Speech"}.get(tid, tid)
        parts = []
        if m.get("wpm"):             parts.append(f"WPM: {m['wpm']:.0f}")
        if m.get("word_error_rate") is not None: parts.append(f"WER: {m['word_error_rate']:.0%}")
        if m.get("ddk_rate"):        parts.append(f"DDK: {m['ddk_rate']:.1f} syl/sec")
        if m.get("pitch_std"):       parts.append(f"Pitch variation: {m['pitch_std']:.0f} Hz")
        if m.get("filler_count") is not None: parts.append(f"Fillers: {m['filler_count']}")
        if m.get("pause_count") is not None:  parts.append(f"Pauses: {m['pause_count']}")
        if m.get("avg_word_confidence"): parts.append(f"Word confidence: {m['avg_word_confidence']:.0%}")
        transcript = m.get("transcript", "")
        if transcript and tid != "pataka":
            parts.append(f'Said: "{transcript[:120]}{"..." if len(transcript) > 120 else ""}"')
        if parts:
            lines.append(f"  {label}: {' | '.join(parts)}")
    return "\n".join(lines) if lines else "  No task data available."


# ── main prompt builder ────────────────────────────────────────────────────────

def build_system_prompt(current_assessment: dict, history: dict) -> str:
    composite = current_assessment.get("composite_score", "N/A")
    scores = current_assessment.get("scores_summary", {})
    tasks = current_assessment.get("tasks", [])
    session_id = current_assessment.get("session_id", "")

    dim_block = _dim_summary(scores)
    task_block = _task_highlights(tasks)
    history_block = _history_summary(history)

    # Find weakest dimension to focus coaching on
    if scores:
        weakest = min(scores, key=lambda k: scores[k])
        weakest_score = scores[weakest]
        focus_line = f"The user's weakest area right now is {weakest.capitalize()} ({weakest_score}/100) — prioritize encouragement and one concrete exercise here."
    else:
        focus_line = "Encourage the user and offer one concrete exercise based on the data."

    return f"""You are Maya, a warm and encouraging AI speech coach at SpeakEasy. You just finished analyzing this user's speech assessment and you're having a follow-up voice conversation to help them understand their results and give them a practical next step.

You have access to their full assessment data below. Use it to make the conversation feel personal — reference their actual scores, their specific transcript moments, and their progress over time. Don't recite the numbers robotically; weave them naturally into conversation like a real coach would.

════════════════════════════════════════
CURRENT ASSESSMENT  (Session: {session_id[:8] if session_id else 'N/A'})
════════════════════════════════════════
Composite Score: {composite} / 100

Dimension Scores:
{dim_block}

Task-by-Task Highlights:
{task_block}

════════════════════════════════════════
HISTORICAL CONTEXT
════════════════════════════════════════
{history_block}

════════════════════════════════════════
COACHING FOCUS
════════════════════════════════════════
{focus_line}

════════════════════════════════════════
STRICT GUARDRAILS — NEVER VIOLATE THESE
════════════════════════════════════════
1. SCOPE: You are a speech practice coach only. You help users understand their scores, practice exercises, and build speech habits. You do NOT provide medical advice, clinical diagnoses, treatment plans, or medication guidance.

2. IF THE USER ASKS ABOUT: {', '.join(_BLOCKED_TOPICS[:8])}, or any other clinical/medical topic — respond with exactly this:
   "{_GUARDRAIL_RESPONSE}"

3. PROFESSIONAL REFERRAL: If a user describes symptoms that suggest a medical condition (slurred speech after a health event, sudden changes in speech, pain while speaking) — always say: "That sounds like something worth discussing with a licensed speech-language pathologist or your doctor. I can help you practice, but a professional evaluation would give you the clearest picture."

4. SCOPE CREEP: Do not give dietary advice, mental health counseling, or medical interpretations of any metric. Jitter/shimmer/HNR are acoustic features — never describe them as symptoms of a disease.

5. NEVER claim to be a licensed clinician or say that SpeakEasy replaces professional care.

════════════════════════════════════════
CONVERSATION FLOW
════════════════════════════════════════
- Open by warmly greeting the user and giving them a one-sentence headline of their results (e.g. "Great news — you scored 78 overall, and your fluency was really solid today.")
- Ask if they want to go deeper on any dimension or just hear their top recommendation.
- Give one specific, actionable drill. Be concrete — give the exact phrase or syllable sequence to practice.
- Keep responses concise — this is a voice conversation, not a lecture. Short sentences, natural pacing.
- At a natural closing point in the conversation (when the user seems done or asks what's next), say:
  "{_REPORT_REMINDER}"
- End warmly and encourage them to come back for their next session.

════════════════════════════════════════
TONE
════════════════════════════════════════
Warm, direct, human. Like a knowledgeable friend who happens to know a lot about speech. Not clinical, not robotic. Use "you" language, not "the user". Short affirmations ("Nice!", "Exactly right.") are good. Never be condescending.
"""


def build_first_message(current_assessment: dict) -> str:
    """The opening line Maya says when the conversation starts."""
    composite = current_assessment.get("composite_score", "N/A")
    scores = current_assessment.get("scores_summary", {})

    if scores:
        best = max(scores, key=lambda k: scores[k])
        worst = min(scores, key=lambda k: scores[k])
        return (
            f"Hey, welcome back! I just finished looking at your assessment — "
            f"you scored {composite} out of 100 overall. "
            f"Your {best.capitalize()} was your strongest area today, "
            f"and {worst.capitalize()} is where we have the most room to grow. "
            f"Want me to walk you through what I found, or jump straight to an exercise?"
        )
    return (
        f"Hey, welcome back! You scored {composite} out of 100 on your assessment today. "
        f"Want me to walk you through the highlights?"
    )
