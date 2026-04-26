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


_METRIC_LABELS = {
    "wpm": ("WPM", "words/min", "130–160"),
    "word_error_rate": ("Word Error Rate", "%", "<10%"),
    "ddk_rate": ("DDK rate", "syl/sec", "5–7"),
    "pitch_std": ("Pitch variation", "Hz", "20–55"),
    "avg_word_confidence": ("Word confidence", "%", ">85%"),
}


def _history_summary(history: dict) -> str:
    if not history or history.get("sessions_completed", 0) == 0:
        return "This is the user's first session — no historical data yet."

    n = history["sessions_completed"]
    streak = history.get("current_streak", 0)
    longest = history.get("longest_streak", 0)
    lines = [
        f"  - Sessions completed: {n}",
        f"  - Practice streak: {streak} day(s) current  |  {longest} day(s) longest ever",
    ]

    # Score trend
    trend = history.get("score_trend", [])
    if len(trend) >= 2:
        first = trend[0].get("overall", "?")
        last = trend[-1].get("overall", "?")
        if isinstance(first, (int, float)) and isinstance(last, (int, float)):
            delta = round(last - first, 1)
            direction = f"+{delta}" if delta >= 0 else str(delta)
            lines.append(f"  - Overall score since first session: {first} → {last} ({direction})")
        recent = [e["overall"] for e in trend[-3:] if e.get("overall") is not None]
        if len(recent) >= 2:
            lines.append(f"  - Recent session scores: {' → '.join(str(s) for s in recent)}")
    elif len(trend) == 1:
        lines.append(f"  - Previous session score: {trend[0].get('overall', 'N/A')}")

    # All 5 dimension averages
    dim_avgs = history.get("dimension_averages", {})
    if dim_avgs:
        order = ["fluency", "clarity", "rhythm", "prosody", "pronunciation"]
        worst = min(dim_avgs, key=lambda k: dim_avgs[k])
        best = max(dim_avgs, key=lambda k: dim_avgs[k])
        lines.append("  - Historical dimension averages:")
        for d in order:
            if d in dim_avgs:
                tag = " ← weakest" if d == worst else (" ← strongest" if d == best else "")
                lines.append(f"    {d.capitalize()}: {dim_avgs[d]}/100{tag}")

    # Metric trends: historical avg → most recent
    metric_trends = history.get("metric_trends", {})
    if metric_trends:
        lines.append("  - Key metric trends (historical avg → most recent):")
        for key, info in metric_trends.items():
            avg = info["average"]
            latest = info["latest"]
            n_tracked = info["sessions_tracked"]
            label, unit, benchmark = _METRIC_LABELS.get(key, (key, "", ""))
            if key in ("word_error_rate", "avg_word_confidence"):
                avg_fmt, latest_fmt = f"{avg:.0%}", f"{latest:.0%}"
            else:
                avg_fmt, latest_fmt = f"{avg:.1f}", f"{latest:.1f}"
            arrow = "↑" if latest > avg else ("↓" if latest < avg else "→")
            lines.append(
                f"    {label}: avg {avg_fmt} → latest {latest_fmt} {arrow}"
                f"  (benchmark: {benchmark}, {n_tracked} session(s) tracked)"
            )

    # Recurring unclear words
    recurring = history.get("recurring_low_confidence_words", [])
    if recurring:
        word_list = ", ".join(
            f'"{w["word"]}" ({w["avg_confidence"]:.0%} conf, {w["occurrences"]}x)'
            for w in recurring[:6]
        )
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
    display_name = history.get("display_name") or None
    goals = history.get("goals")

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

    name_line = f"Address the user by their name: {display_name}.\n" if display_name else ""
    goals_line = f"User's stated goals: {goals}\n" if goals else ""

    return f"""You are Alex, a warm and encouraging AI speech coach at SpeakEasy. You just finished analyzing this user's speech assessment and you're having a follow-up voice conversation to help them understand their results and give them a practical next step.
{name_line}{goals_line}
════════════════════════════════════════
BREVITY — HARD RULE (read this first)
════════════════════════════════════════
THIS IS A VOICE CONVERSATION. NEVER GIVE MORE THAN 2 SENTENCES IN A SINGLE TURN.
After every 1–2 sentences, STOP and ask the user a question or wait for their response.
Do NOT list multiple things at once. Do NOT summarize everything upfront.
Deliver one idea, then pause. The user will ask for more if they want it.
VIOLATION EXAMPLE (FORBIDDEN): "You scored 72 overall. Your fluency was your strongest area at 81, and your rhythm was your weakest at 58. I'd recommend working on pa-ta-ka drills — try saying pa-ta-ka 5 times fast. You can also try..."
CORRECT EXAMPLE: "You scored 72 overall — pretty solid! Want me to break down your strongest and weakest areas?"

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
- Open with ONE sentence: their score + one observation. Then ask one question. Stop.
- Never volunteer more than one piece of information per turn.
- Give drills only when asked, or when explicitly transitioning to "here's your exercise". One drill only.
- MAX 2 sentences per turn — always end with a question or clear pause for the user.
- At a natural closing point, say: "{_REPORT_REMINDER}"
- End warmly.

════════════════════════════════════════
TONE
════════════════════════════════════════
Warm, direct, human. Like a knowledgeable friend who knows speech. Not clinical, not robotic. Use "you" not "the user". Short affirmations ("Nice!", "Exactly.") are good. Never be condescending. Less is always more — if you can cut a word, cut it.
"""


def build_first_message(current_assessment: dict) -> str:
    """The opening line Alex says when the conversation starts."""
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
