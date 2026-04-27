import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

THERAPIST_AGENT_ADDRESS = os.getenv("THERAPIST_AGENT_ADDRESS", "")

agent = Agent(
    name="progress_tracker",
    seed=os.getenv("AGGREGATE_AGENT_SEED", "speakeasy_aggregate_agent_seed"),
    port=8032,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


# ── Supabase history fetch ─────────────────────────────────────────────────────

def _fetch_history(user_id: str, exclude_session_id: str) -> dict:
    """
    Pull all past completed sessions for this user from Supabase.
    Returns a structured summary of longitudinal trends.
    """
    try:
        from backend.db.queries import get_dashboard_data
        data = get_dashboard_data(user_id)
    except Exception as exc:
        return {"error": f"Supabase fetch failed: {exc}"}

    sessions = data.get("sessions", [])
    assessments = data.get("assessments", [])

    # Exclude the current session (just completed, already in new_assessment payload)
    past_sessions = [s for s in sessions if s["id"] != exclude_session_id]
    if not past_sessions:
        return {"sessions_completed": 0, "message": "This is your first session."}

    past_session_ids = {s["id"] for s in past_sessions}
    past_assessments = [a for a in assessments if a["session_id"] in past_session_ids]

    # Score trend: overall score per session over time
    score_trend = [
        {"date": s["created_at"][:10], "overall": s.get("overall_score")}
        for s in past_sessions if s.get("overall_score") is not None
    ]

    # Dimension averages across all past sessions
    dim_keys = ["score_fluency", "score_clarity", "score_rhythm",
                "score_prosody", "score_pronunciation"]
    dim_totals: dict[str, list] = {k: [] for k in dim_keys}
    for a in past_assessments:
        for k in dim_keys:
            if a.get(k) is not None:
                dim_totals[k].append(a[k])

    dim_averages = {
        k.replace("score_", ""): round(sum(v) / len(v), 1)
        for k, v in dim_totals.items() if v
    }

    # Recurring low-confidence words across past sessions
    word_freq: dict[str, list] = {}
    for a in past_assessments:
        for w in (a.get("low_confidence_words") or []):
            word = w.get("word", "").lower().strip(".,!?'\"")
            if word:
                word_freq.setdefault(word, []).append(w.get("confidence", 0))
    recurring_words = sorted(
        [{"word": w, "avg_confidence": round(sum(c) / len(c), 2), "occurrences": len(c)}
         for w, c in word_freq.items() if len(c) >= 2],
        key=lambda x: x["avg_confidence"]
    )[:8]

    # Key metric trends (most recent vs average)
    metric_keys = ["wpm", "word_error_rate", "ddk_rate", "pitch_std", "avg_word_confidence"]
    metric_trends: dict[str, dict] = {}
    for mk in metric_keys:
        vals = [a[mk] for a in past_assessments if a.get(mk) is not None]
        if vals:
            metric_trends[mk] = {
                "average": round(sum(vals) / len(vals), 3),
                "latest": vals[-1],
                "sessions_tracked": len(vals),
            }

    return {
        "sessions_completed": len(past_sessions),
        "current_streak": data.get("current_streak", 0),
        "longest_streak": data.get("longest_streak", 0),
        "display_name": data.get("display_name"),
        "goals": data.get("goals"),
        "score_trend": score_trend,
        "dimension_averages": dim_averages,
        "recurring_low_confidence_words": recurring_words,
        "metric_trends": metric_trends,
    }


# ── agent message handlers ─────────────────────────────────────────────────────

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Progress Tracker received assessment ({len(text)} chars)")

    try:
        new_assessment = json.loads(text)
    except json.JSONDecodeError as exc:
        ctx.logger.error(f"Failed to parse assessment JSON: {exc}")
        return

    user_id = new_assessment.get("user_id", "")
    session_id = new_assessment.get("session_id", "")

    if not user_id:
        ctx.logger.warning("No user_id in payload — cannot fetch history from Supabase")
        history = {"sessions_completed": 0, "message": "No user_id provided."}
    else:
        ctx.logger.info(f"Fetching history for user {user_id[:16]}... from Supabase")
        history = _fetch_history(user_id, exclude_session_id=session_id)
        ctx.logger.info(
            f"History: {history.get('sessions_completed', 0)} past sessions, "
            f"streak: {history.get('current_streak', 0)}"
        )

    # Forward current assessment + longitudinal context to therapist
    payload = {
        "current_assessment": new_assessment,
        "history": history,
    }

    # Always save prompt to file for debugging / teammate handoff
    try:
        from backend.agents.therapist_agent.prompt_builder import build_system_prompt, build_first_message
        system_prompt = build_system_prompt(new_assessment, history)
        first_message = build_first_message(new_assessment)
        os.makedirs("backend/debug", exist_ok=True)
        with open("backend/debug/therapist_prompt.txt", "w") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Session: {session_id}\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            f.write("── FIRST MESSAGE ──\n\n")
            f.write(first_message + "\n\n")
            f.write("── SYSTEM PROMPT ──\n\n")
            f.write(system_prompt + "\n")
        ctx.logger.info("Therapist prompt saved to backend/debug/therapist_prompt.txt")
    except Exception as exc:
        ctx.logger.warning(f"Could not save therapist prompt: {exc}")

    ctx.logger.info("Prompt saved. Therapist session is initiated by frontend via /api/therapist/session.")


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent._logger.info(f"Progress Tracker address: {agent.address}")
    agent.run()
