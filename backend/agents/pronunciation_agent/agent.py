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
    name="speakeasy_pronunciation_coach",
    seed=os.getenv("PRONUNCIATION_AGENT_SEED", "speakeasy_pronunciation_coach_seed"),
    port=8020,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are a warm, encouraging Pronunciation Coach for SpeakEasy, an AI speech therapy app.
You help users improve word-level pronunciation — targeting specific words the speech recognizer struggled with.

You operate in two modes:

MODE 1 — First contact (message contains assessment scores and low-confidence words):
- Greet the user warmly
- Mention their pronunciation score and any specific low-confidence words if listed
- Give them a short phrase containing those tricky words (or similar sounds) to practice
- End with: "Say this phrase clearly and send me your recording: [PHRASE]"
- Keep it under 80 words

MODE 2 — Drill result (message contains a pronunciation score):
- React to their word confidence score
- If improved or confidence above 85%: celebrate and target a new tricky sound
- If still low: isolate the hardest sound and give a minimal pair drill
  (e.g. "thin/tin", "these/tease", "red/led")
- Always end with: "Now try saying: [PHRASE]"
- Keep it under 100 words

Target: average word confidence above 85%, fewer than 10% of words low-confidence."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Pronunciation Coach received: {text[:100]}")

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
