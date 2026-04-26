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

from .gemma_client import build_system_prompt

load_dotenv()

agent = Agent(
    name="speakeasy_therapist",
    seed=os.getenv("THERAPIST_AGENT_SEED", "speakeasy_therapist_seed"),
    port=8021,
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
    ctx.logger.info(f"Therapist agent received: {text[:100]}")

    try:
        payload = json.loads(text)
        assessment = payload.get("assessment", {})
        history = payload.get("history", {})
        system_prompt = build_system_prompt(assessment, history)
        reply = json.dumps({"system_prompt": system_prompt})
    except json.JSONDecodeError:
        ctx.logger.error("Therapist agent: could not parse JSON input")
        reply = json.dumps({"error": "Invalid JSON payload — expected {assessment, history}"})
    except Exception as e:
        ctx.logger.error(f"Therapist agent error: {e}")
        reply = json.dumps({"error": str(e)})

    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=reply),
            EndSessionContent(type="end-session"),
        ],
    ))


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
