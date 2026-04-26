import json
import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from backend.agents.orchestrator_agent.gemma_client import generate_narrative
from backend.agents.orchestrator_agent.pdf_generator import generate_pdf

load_dotenv()

# ── Coach agent addresses (fill in after deploying each to Agentverse) ──────
COACH_ADDRESSES = {
    "fluency":       os.getenv("FLUENCY_AGENT_ADDRESS", ""),
    "clarity":       os.getenv("CLARITY_AGENT_ADDRESS", ""),
    "rhythm":        os.getenv("RHYTHM_AGENT_ADDRESS", ""),
    "prosody":       os.getenv("PROSODY_AGENT_ADDRESS", ""),
    "pronunciation": os.getenv("PRONUNCIATION_AGENT_ADDRESS", ""),
}

GOOD_SCORE_THRESHOLD = 90.0  # all dimensions above this → skip coaching

agent = Agent(
    name="speakeasy_orchestrator",
    seed=os.getenv("AGENT_SEED", "speechscore_orchestrator_unique_seed_phrase"),
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


def _scores_from_payload(assessment: dict) -> dict[str, float]:
    """Extract per-dimension scores from either old or new assessment format."""
    # New 3-task format
    if "scores_summary" in assessment:
        return assessment["scores_summary"]
    # Old flat format
    s = assessment.get("scores", {})
    return {k: v for k, v in s.items() if k != "overall" and v is not None}


def _coaches_needed(scores: dict[str, float]) -> list[tuple[str, float]]:
    """Return (dimension, score) pairs below threshold, sorted worst first."""
    low = [(dim, score) for dim, score in scores.items() if score < GOOD_SCORE_THRESHOLD]
    return sorted(low, key=lambda x: x[1])


def _build_coach_context(dimension: str, score: float, assessment: dict) -> str:
    """Build the opening message sent to a coach agent."""
    scores_summary = _scores_from_payload(assessment)
    composite = assessment.get("composite_score", assessment.get("scores", {}).get("overall", "N/A"))

    # Pull relevant metrics for this dimension from tasks
    metrics_lines = []
    for task in assessment.get("tasks", []):
        m = task.get("metrics", {})
        if dimension == "fluency" and m.get("wpm"):
            metrics_lines.append(f"WPM: {m['wpm']} (task: {task['task_id']})")
        if dimension == "fluency" and m.get("filler_count"):
            metrics_lines.append(f"Filler words: {m['filler_count']}")
        if dimension == "clarity" and m.get("word_error_rate") is not None:
            metrics_lines.append(f"Word error rate: {m['word_error_rate']:.1%}")
        if dimension == "rhythm" and m.get("ddk_rate"):
            metrics_lines.append(f"DDK rate: {m['ddk_rate']} syl/sec (normal: 5–7)")
            metrics_lines.append(f"Rhythm regularity: {m.get('rhythm_regularity', 'N/A')}")
        if dimension == "prosody" and m.get("pitch_std_hz"):
            metrics_lines.append(f"Pitch variation: {m['pitch_std_hz']} Hz std (expressive: 20–55 Hz)")
        if dimension == "pronunciation" and m.get("avg_word_confidence"):
            metrics_lines.append(f"Word confidence: {m['avg_word_confidence']:.1%}")
        if dimension == "pronunciation" and m.get("low_confidence_words"):
            words = [w["word"] for w in m["low_confidence_words"][:5]]
            metrics_lines.append(f"Low-confidence words: {words}")

    metrics_block = "\n".join(metrics_lines) if metrics_lines else "No detailed metrics available."

    return f"""New user needs coaching. Here are their assessment results:

Composite score: {composite}/100
All dimension scores: {json.dumps(scores_summary, indent=2)}

This user scored {score}/100 on {dimension.upper()} — this is why you were activated.

Relevant metrics for {dimension}:
{metrics_block}

Please introduce yourself as their {dimension.capitalize()} Coach and give them one specific
drill phrase or exercise to try right now. Keep it warm, encouraging, and under 100 words.
End with the exact phrase or sentence you want them to say aloud."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Orchestrator received: {text[:100]}...")

    response_text = "Assessment received."
    try:
        assessment = json.loads(text)

        # ── Generate Gemma narrative + PDF ───────────────────
        ctx.logger.info("Generating Gemma narrative...")
        narrative = generate_narrative(assessment)
        os.makedirs("backend/reports", exist_ok=True)
        session_id = assessment.get("session_id", "session")
        generate_pdf(assessment, narrative, f"backend/reports/{session_id}.pdf")
        ctx.logger.info(f"PDF saved: backend/reports/{session_id}.pdf")

        # ── Check if coaching is needed ───────────────────────
        scores = _scores_from_payload(assessment)
        coaches_needed = _coaches_needed(scores)

        if not coaches_needed:
            ctx.logger.info("All scores above 90 — no coaching needed.")
            response_text = (
                f"Excellent work! All your scores are above 90/100. "
                f"{narrative.get('overall_summary', '')} "
                f"Your PDF report has been saved."
            )
        else:
            dims = [d for d, _ in coaches_needed]
            ctx.logger.info(f"Activating coaches for: {dims}")

            # Message each needed coach agent
            for dimension, score in coaches_needed:
                address = COACH_ADDRESSES.get(dimension, "")
                if not address:
                    ctx.logger.warning(f"No address for {dimension} coach — skipping")
                    continue
                coach_msg = _build_coach_context(dimension, score, assessment)
                await ctx.send(address, ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=coach_msg)],
                ))
                ctx.logger.info(f"Sent to {dimension} coach at {address[:30]}...")

            response_text = (
                f"{narrative.get('overall_summary', '')}\n\n"
                f"Activating coaches for: {', '.join(dims)}. "
                f"Your PDF report has been saved."
            )

    except json.JSONDecodeError:
        ctx.logger.error("Could not parse assessment JSON")
        response_text = "Error: could not parse assessment data."
    except Exception:
        ctx.logger.exception("Orchestrator pipeline error")
        response_text = "Something went wrong processing your assessment."

    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response_text),
            EndSessionContent(type="end-session"),
        ],
    ))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent._logger.info(f"Agent address: {agent.address}")
    agent.run()
