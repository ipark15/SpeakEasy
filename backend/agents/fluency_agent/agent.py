import json
import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from google import genai
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

gemma = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

agent = Agent(
    name="speakeasy_fluency_coach",
    seed=os.getenv("FLUENCY_AGENT_SEED", "speakeasy_fluency_coach_seed"),
    port=8011,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are a warm, encouraging Fluency Coach for SpeakEasy, an AI speech therapy app.
You help users improve speaking fluency: pace (WPM), filler words (um/uh), and pause patterns.

You operate in two modes:

MODE 1 — First contact (message contains assessment scores):
- Greet the user warmly
- Briefly explain their fluency score in plain language
- Give them ONE specific phrase to say aloud as a drill
- End with: "Say this phrase aloud and send me your recording: [PHRASE]"
- Keep it under 80 words

MODE 2 — Drill result (message contains a fluency score from their recording):
- React to their score with specific encouragement or correction
- If score improved or is above 75: celebrate and give a harder drill phrase
- If score still low: give a simpler drill and a tip (e.g. "slow down between words")
- Always end with the next phrase to try: "Now try: [PHRASE]"
- Keep it under 100 words

Target metrics: 120–160 WPM, fewer than 2 filler words per minute, pauses only at punctuation."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Fluency Coach received: {text[:100]}")

    try:
        response = gemma.models.generate_content(
            model="gemma-2-9b-it",
            contents=f"{SYSTEM_PROMPT}\n\nUser message:\n{text}",
        )
        reply = response.text.strip()
    except Exception as e:
        ctx.logger.error(f"Gemma error: {e}")
        reply = "I'm having trouble connecting right now — please try again in a moment!"

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
