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

ORCHESTRATOR_ADDRESS = os.getenv("ORCHESTRATOR_AGENT_ADDRESS", "")

agent = Agent(
    name="speakeasy_assessment",
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
    ctx.logger.info(f"Assessment Agent received scores payload ({len(text)} chars), forwarding to orchestrator")

    if not ORCHESTRATOR_ADDRESS:
        ctx.logger.error("ORCHESTRATOR_AGENT_ADDRESS not set — cannot forward")
        return

    await ctx.send(ORCHESTRATOR_ADDRESS, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    ))
    ctx.logger.info(f"Forwarded to orchestrator at {ORCHESTRATOR_ADDRESS[:30]}...")


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent._logger.info(f"Assessment Agent address: {agent.address}")
    agent.run()
