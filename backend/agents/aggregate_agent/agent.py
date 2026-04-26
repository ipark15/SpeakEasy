import json
import os
import re
from datetime import datetime, timezone
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

AGGREGATE_PATH = "backend/aggregate_data/aggregate.json"
THERAPIST_AGENT_ADDRESS = os.getenv("THERAPIST_AGENT_ADDRESS", "")

agent = Agent(
    name="speakeasy_aggregate",
    seed=os.getenv("AGGREGATE_AGENT_SEED", "speakeasy_aggregate_agent_seed"),
    port=8032,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


# ── aggregation helpers ────────────────────────────────────────────────────────

def _normalize_word(w: str) -> str:
    return re.sub(r"^[^\w]+|[^\w]+$", "", w.lower())


def _avg(a: float, b: float) -> float:
    return round((a + b) / 2, 3)


def _merge_low_confidence_words(existing: list, new: list) -> list:
    merged: dict[str, dict] = {_normalize_word(item["word"]): item for item in existing}
    for item in new:
        key = _normalize_word(item["word"])
        if key in merged:
            merged[key] = {
                "word": item["word"],
                "confidence": _avg(merged[key]["confidence"], item["confidence"]),
            }
        else:
            merged[key] = item
    return list(merged.values())


def _merge_metrics(existing: dict, new: dict) -> dict:
    result = dict(existing)
    for key, new_val in new.items():
        if key not in result:
            result[key] = new_val
            continue
        old_val = result[key]
        if key == "low_confidence_words":
            result[key] = _merge_low_confidence_words(old_val, new_val)
        elif isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
            result[key] = _avg(old_val, new_val)
        elif isinstance(old_val, str) and isinstance(new_val, str):
            if old_val == new_val:
                result[key] = old_val
            else:
                result[key] = list({old_val, new_val})
        elif isinstance(old_val, list) and isinstance(new_val, list):
            result[key] = old_val + new_val
        elif isinstance(old_val, list):
            if new_val not in old_val:
                result[key] = old_val + [new_val]
        else:
            result[key] = new_val
    return result


def _merge_metadata(existing: dict, new: dict) -> dict:
    result = dict(existing)
    for key, new_val in new.items():
        if key not in result:
            result[key] = new_val
            continue
        old_val = result[key]
        if isinstance(old_val, str) and isinstance(new_val, str):
            result[key] = old_val if old_val == new_val else list({old_val, new_val})
        elif isinstance(old_val, list):
            if new_val not in old_val:
                result[key] = old_val + [new_val]
        else:
            result[key] = new_val
    return result


def _merge_scores(existing: dict, new: dict) -> dict:
    result = dict(existing)
    for key, new_val in new.items():
        if key not in result:
            result[key] = new_val
        elif isinstance(new_val, (int, float)) and isinstance(result[key], (int, float)):
            result[key] = _avg(result[key], new_val)
    return result


def _merge_assessments(existing: dict, new: dict) -> dict:
    result = {
        "assessed_at": new["assessed_at"],
        "composite_score": _avg(existing["composite_score"], new["composite_score"]),
        "scores_summary": _merge_scores(
            existing.get("scores_summary", {}), new.get("scores_summary", {})
        ),
    }

    existing_tasks = {t["task_id"]: t for t in existing.get("tasks", [])}
    new_tasks = {t["task_id"]: t for t in new.get("tasks", [])}

    merged_tasks = []
    for task_id, new_task in new_tasks.items():
        if task_id not in existing_tasks:
            merged_tasks.append(new_task)
        else:
            old_task = existing_tasks[task_id]
            merged_tasks.append({
                "task_id": task_id,
                "metadata": _merge_metadata(
                    old_task.get("metadata", {}), new_task.get("metadata", {})
                ),
                "scores": _merge_scores(
                    old_task.get("scores", {}), new_task.get("scores", {})
                ),
                "metrics": _merge_metrics(
                    old_task.get("metrics", {}), new_task.get("metrics", {})
                ),
            })
    for task_id, old_task in existing_tasks.items():
        if task_id not in new_tasks:
            merged_tasks.append(old_task)

    result["tasks"] = merged_tasks
    return result


# ── agent message handlers ─────────────────────────────────────────────────────

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id,
    ))

    text = "".join(item.text for item in msg.content if isinstance(item, TextContent))
    ctx.logger.info(f"Aggregate Agent received assessment ({len(text)} chars)")

    try:
        new_assessment = json.loads(text)
    except json.JSONDecodeError as exc:
        ctx.logger.error(f"Failed to parse assessment JSON: {exc}")
        return

    existing = None
    if os.path.exists(AGGREGATE_PATH):
        try:
            with open(AGGREGATE_PATH, "r") as f:
                existing = json.load(f)
        except Exception as exc:
            ctx.logger.warning(f"Could not read existing aggregate, starting fresh: {exc}")

    aggregate = new_assessment if existing is None else _merge_assessments(existing, new_assessment)

    os.makedirs(os.path.dirname(AGGREGATE_PATH), exist_ok=True)
    with open(AGGREGATE_PATH, "w") as f:
        json.dump(aggregate, f, indent=2)
    ctx.logger.info("Aggregate JSON updated")

    if THERAPIST_AGENT_ADDRESS:
        await ctx.send(THERAPIST_AGENT_ADDRESS, ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=json.dumps(aggregate))],
        ))
        ctx.logger.info(f"Forwarded aggregate to therapist at {THERAPIST_AGENT_ADDRESS[:30]}...")
    else:
        ctx.logger.warning("THERAPIST_AGENT_ADDRESS not set — aggregate not forwarded")


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent._logger.info(f"Aggregate Agent address: {agent.address}")
    agent.run()
