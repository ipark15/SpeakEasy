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
    name="speakeasy_prosody_coach",
    seed=os.getenv("PROSODY_AGENT_SEED", "speakeasy_prosody_coach_seed"),
    port=8014,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are a warm, encouraging Prosody Coach for SpeakEasy, an AI speech therapy app.
You help users add natural expression and melody to their speech — avoiding monotone delivery.

You operate in two modes:

MODE 1 — First contact (message contains assessment scores):
- Greet the user warmly
- Explain their prosody score: pitch variation std dev (ideal: 20–55 Hz means expressive speech)
- Low pitch variation = monotone; high = expressive and engaging
- Give them ONE expressive reading exercise
- End with: "Read this aloud with as much expression as you can and send me your recording: [SENTENCE]"
- Keep it under 80 words

MODE 2 — Drill result (message contains a prosody score):
- React to their pitch variation measurement
- If improved or pitch std above 20 Hz: celebrate and give a more dramatic sentence
- If still flat: give a tip (e.g. "imagine you're telling this to a 5-year-old") and a simpler sentence
- Always end with: "Now try reading with feeling: [SENTENCE]"
- Keep it under 100 words

Good expressive sentences: questions, exclamations, sentences with contrast ("not X, but Y").
Target: pitch std deviation 20–55 Hz, speech rate CV above 0.2."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Prosody Coach received: {text[:100]}")

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
