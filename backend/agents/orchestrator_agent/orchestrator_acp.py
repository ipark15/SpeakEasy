import json
import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI
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

# ASI1 client — used as the chat interface
asi1_client = OpenAI(
    base_url="https://api.asi1.ai/v1",
    api_key=os.getenv("ASI1_API_KEY"),
)

agent = Agent(
    name="speechscore_orchestrator",
    seed=os.getenv("AGENT_SEED", "speechscore_orchestrator_unique_seed_phrase"),
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are SpeechScore, an AI speech assessment orchestrator powered by Gemma 4.
Your job is to receive speech assessment data (scores and acoustic features) and return a
patient-friendly analysis of the results.

When given assessment JSON, you will:
1. Explain what each score means in plain, encouraging language
2. Identify the speaker's strongest and weakest areas
3. Highlight specific moments where the speaker struggled
4. Provide 3 actionable practice recommendations
5. Generate a PDF report summarizing all findings

You work with these speech metrics: fluency, clarity, rhythm, prosody, voice quality,
word error rate, DDK rate, rhythm regularity, speaking rate (WPM), pitch variation,
jitter, shimmer, and harmonics-to-noise ratio (HNR).

If asked about therapy sessions or coach agents, let the user know that personalized
therapy coaching (Rhythm Coach, Clarity Coach, Fluency Coach, Prosody Coach) is coming
soon as a Phase 2 feature."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text

    ctx.logger.info(f"Received message: {text[:100]}...")

    response_text = "Something went wrong while processing your speech assessment."
    try:
        # Try to parse as assessment JSON first
        assessment = None
        try:
            assessment = json.loads(text)
        except json.JSONDecodeError:
            pass

        if assessment and "scores" in assessment:
            # Full pipeline: Gemma narrative + PDF
            ctx.logger.info("Running full Gemma pipeline...")
            narrative = generate_narrative(assessment)

            os.makedirs("backend/reports", exist_ok=True)
            session_id = assessment.get("session_id", "session")
            generate_pdf(assessment, narrative, f"backend/reports/{session_id}.pdf")

            response_text = (
                f"**SpeechScore Assessment Complete**\n\n"
                f"Overall Score: {assessment['scores']['overall']} / 100\n\n"
                f"{narrative.get('overall_summary', '')}\n\n"
                f"**Strengths:**\n{narrative.get('strengths', '')}\n\n"
                f"**Areas to Improve:**\n{narrative.get('weaknesses', '')}\n\n"
                f"**Recommended Focus:**\n{narrative.get('next_focus', '')}\n\n"
                f"PDF report saved to backend/reports/{session_id}.pdf"
            )
        else:
            # Plain chat — use ASI1 directly
            r = asi1_client.chat.completions.create(
                model="asi1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                max_tokens=1024,
            )
            response_text = str(r.choices[0].message.content)

    except Exception:
        ctx.logger.exception("Error in orchestrator pipeline")

    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    ctx_logger = agent._logger
    ctx_logger.info(f"Agent address: {agent.address}")
    agent.run()
