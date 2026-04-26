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


agent = Agent(
    name="report_generator",
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

        # pdf_generator expects a flat dict with "scores", "features", "events"
        scores_summary = _scores_from_payload(assessment)
        tasks = assessment.get("tasks", [])
        all_pauses, all_low_conf = [], []
        features: dict = {}
        for t in tasks:
            m = t.get("metrics", {})
            all_pauses.extend(m.get("pauses") or [])
            all_low_conf.extend(m.get("low_confidence_words") or [])
            for k in ("wpm", "word_error_rate", "ddk_rate", "rhythm_regularity", "pitch_std"):
                if k not in features and m.get(k) is not None:
                    features[k] = m[k]

        pdf_input = {
            "user_id":    assessment.get("user_id", ""),
            "session_id": session_id,
            "scores":     {**scores_summary, "overall": assessment.get("composite_score", 0)},
            "features":   features,
            "events":     {"pauses": all_pauses, "low_confidence_words": all_low_conf},
        }
        generate_pdf(pdf_input, narrative, f"backend/reports/{session_id}.pdf")
        ctx.logger.info(f"PDF saved: backend/reports/{session_id}.pdf")

        response_text = (
            f"{narrative.get('overall_summary', '')} "
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
