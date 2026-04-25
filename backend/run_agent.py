import json
import os

from dotenv import load_dotenv
from uagents import Agent, Bureau, Context

load_dotenv()

from backend.agents.orchestrator_agent.orchestrator import orchestrator
from backend.agents.orchestrator_agent.models import AssessmentRequest, ReportResponse

with open("backend/data/dummy_assessment.json") as f:
    dummy_assessment = json.load(f)

sender = Agent(
    name="test_sender",
    seed="test_sender_speechscore_hackathon_seed",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)


@sender.on_event("startup")
async def send_test_assessment(ctx: Context):
    ctx.logger.info("Sending dummy assessment to orchestrator...")
    await ctx.send(
        orchestrator.address,
        AssessmentRequest(
            session_id=dummy_assessment["session_id"],
            assessment_json=json.dumps(dummy_assessment),
        ),
    )


@sender.on_message(model=ReportResponse)
async def receive_report(ctx: Context, sender_addr: str, msg: ReportResponse):
    ctx.logger.info("=" * 55)
    ctx.logger.info("REPORT RECEIVED")
    ctx.logger.info(f"Status  : {msg.status}")
    ctx.logger.info(f"PDF path: {msg.pdf_path}")
    ctx.logger.info(f"Summary : {msg.summary[:300]}...")
    ctx.logger.info("=" * 55)


bureau = Bureau()
bureau.add(orchestrator)
bureau.add(sender)

if __name__ == "__main__":
    bureau.run()
