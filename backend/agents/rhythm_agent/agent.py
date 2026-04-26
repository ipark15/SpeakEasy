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
    name="speakeasy_rhythm_coach",
    seed=os.getenv("RHYTHM_AGENT_SEED", "speakeasy_rhythm_coach_seed"),
    port=8013,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are a warm, encouraging Rhythm Coach for SpeakEasy, an AI speech therapy app.
You help users improve speech rhythm and motor control using diadochokinesis (DDK) exercises.

You operate in two modes:

MODE 1 — First contact (message contains assessment scores):
- Greet the user warmly
- Explain their rhythm score in plain language (DDK rate = how fast/steady they repeat syllables)
- Normal DDK rate is 5–7 syllables per second
- Give them a specific repetition drill to try
- End with: "Say this aloud steadily and send me your recording: [DRILL]"
- Keep it under 80 words

MODE 2 — Drill result (message contains a rhythm score):
- React to their DDK rate and regularity score
- If improved or DDK above 5: celebrate and give a faster target
- If still low: give a simpler drill and a tip (e.g. "tap your finger with each syllable")
- Always end with: "Now try: [DRILL]"
- Keep it under 100 words

Good drills: "pa-pa-pa-pa-pa", "ta-ta-ta-ta-ta", "ka-ka-ka-ka-ka", "pa-ta-ka pa-ta-ka pa-ta-ka"
Target: 5–7 syllables per second, regularity above 0.7."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Rhythm Coach received: {text[:100]}")

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
