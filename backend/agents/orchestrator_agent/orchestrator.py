import json
import os

from uagents import Agent, Context
from dotenv import load_dotenv

from backend.agents.orchestrator_agent.models import AssessmentRequest, ReportResponse
from backend.agents.orchestrator_agent.gemma_client import generate_narrative
from backend.agents.orchestrator_agent.pdf_generator import generate_pdf

load_dotenv()

orchestrator = Agent(
    name="speechscore_orchestrator",
    seed=os.getenv("AGENT_SEED", "speechscore_orchestrator_default_seed"),
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)


@orchestrator.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Orchestrator ready. Address: {orchestrator.address}")


@orchestrator.on_message(model=AssessmentRequest)
async def handle_assessment(ctx: Context, sender: str, msg: AssessmentRequest):
    ctx.logger.info(f"Received assessment — session: {msg.session_id}")

    try:
        assessment = json.loads(msg.assessment_json)

        ctx.logger.info("Calling Gemma API...")
        narrative = generate_narrative(assessment)

        ctx.logger.info("Generating PDF...")
        os.makedirs("reports", exist_ok=True)
        pdf_path = generate_pdf(
            assessment, narrative,
            f"reports/{msg.session_id}.pdf",
        )

        ctx.logger.info(f"PDF saved: {pdf_path}")
        await ctx.send(sender, ReportResponse(
            session_id=msg.session_id,
            pdf_path=pdf_path,
            status="success",
            summary=narrative.get("overall_summary", ""),
        ))

    except Exception as exc:
        ctx.logger.error(f"Pipeline error: {exc}")
        await ctx.send(sender, ReportResponse(
            session_id=msg.session_id,
            pdf_path="",
            status=f"error: {exc}",
            summary="",
        ))
