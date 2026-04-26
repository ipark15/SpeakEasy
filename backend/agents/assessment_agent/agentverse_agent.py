from datetime import datetime
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

ORCHESTRATOR_ADDRESS = "agent1qtz33045rvggwj93lcul6agm2f6rzleudu0j89u3pqsddwp8q7pxy52x7sy"

agent = Agent(
    name="speakeasy_assessment",
    seed="speakeasy_assessment_agent_seed",
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Assessment Agent received scores ({len(text)} chars), forwarding to orchestrator")

    await ctx.send(ORCHESTRATOR_ADDRESS, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=text)],
    ))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)
