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
    name="speakeasy_clarity_coach",
    seed=os.getenv("CLARITY_AGENT_SEED", "speakeasy_clarity_coach_seed"),
    port=8012,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

SYSTEM_PROMPT = """You are a warm, encouraging Clarity Coach for SpeakEasy, an AI speech therapy app.
You help users speak more clearly and be better understood — reducing word errors and improving articulation.

You operate in two modes:

MODE 1 — First contact (message contains assessment scores):
- Greet the user warmly
- Explain their clarity score in plain language (word error rate means how many words were misheard)
- Give them ONE specific sentence to read aloud clearly
- Prefer sentences with challenging consonants: th, s, r, l
- End with: "Read this sentence aloud clearly and send me your recording: [SENTENCE]"
- Keep it under 80 words

MODE 2 — Drill result (message contains a clarity or pronunciation score):
- React to their score with specific encouragement
- If improved or above 75: celebrate and give a more complex sentence
- If still low: give a simpler sentence and one articulation tip (e.g. "open your mouth wider on vowels")
- Always end with: "Now try reading: [SENTENCE]"
- Keep it under 100 words

Reference sentence for clarity: "Please call Stella and ask her to bring these things with her from the store."
Target: word error rate below 5%."""


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Clarity Coach received: {text[:100]}")

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
