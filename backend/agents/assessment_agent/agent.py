import os
from datetime import datetime
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

REPORT_GENERATOR_ADDRESS  = os.getenv("ORCHESTRATOR_AGENT_ADDRESS", "")
PROGRESS_TRACKER_ADDRESS  = os.getenv("PROGRESS_TRACKER_ADDRESS", "")

agent = Agent(
    name="assessment_agent",
    seed=os.getenv("ASSESSMENT_AGENT_SEED", "speakeasy_assessment_agent_seed"),
    port=8031,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Assessment Agent received payload ({len(text)} chars) — fanning out in parallel")

    chat_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    )

    # Fire both simultaneously — uagents send is async so both kick off before either awaits
    if REPORT_GENERATOR_ADDRESS:
        await ctx.send(REPORT_GENERATOR_ADDRESS, ChatMessage(
            timestamp=datetime.utcnow(), msg_id=uuid4(),
            content=[TextContent(type="text", text=text)],
        ))
        ctx.logger.info(f"→ Report Generator: {REPORT_GENERATOR_ADDRESS[:30]}...")
    else:
        ctx.logger.warning("ORCHESTRATOR_AGENT_ADDRESS not set — skipping report generator")

    if PROGRESS_TRACKER_ADDRESS:
        await ctx.send(PROGRESS_TRACKER_ADDRESS, ChatMessage(
            timestamp=datetime.utcnow(), msg_id=uuid4(),
            content=[TextContent(type="text", text=text)],
        ))
        ctx.logger.info(f"→ Progress Tracker:  {PROGRESS_TRACKER_ADDRESS[:30]}...")
    else:
        ctx.logger.warning("PROGRESS_TRACKER_ADDRESS not set — skipping progress tracker")


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent._logger.info(f"Assessment Agent address: {agent.address}")
    agent.run()
