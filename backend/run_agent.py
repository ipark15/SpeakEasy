import glob
import json
import os

from dotenv import load_dotenv
from uagents import Agent, Bureau, Context

load_dotenv()

from backend.agents.orchestrator_agent.orchestrator import orchestrator
from backend.agents.orchestrator_agent.models import AssessmentRequest, ReportResponse


def _load_latest_assessment() -> dict:
    """Load the most recent assessment file from backend/data/."""
    pattern = "backend/data/assessment_*.json"
    files = sorted(glob.glob(pattern))
    if files:
        path = files[-1]
        print(f"[run_agent] Loading assessment: {path}")
        with open(path) as f:
            return json.load(f)
    # Fall back to dummy data
    print("[run_agent] No assessment_*.json found — using dummy_assessment.json")
    with open("backend/data/dummy_assessment.json") as f:
        return json.load(f)


def _normalize(raw: dict) -> dict:
    """Convert test_pipeline.py output schema to orchestrator-expected schema."""
    # Already in old format (dummy or legacy)
    if "scores" in raw and "features" in raw:
        return raw

    ss = raw.get("scores_summary", {})
    scores = {
        "fluency":       ss.get("fluency", 0),
        "clarity":       ss.get("clarity", 0),
        "rhythm":        ss.get("rhythm", 0),
        "prosody":       ss.get("prosody", 0),
        "voice_quality": ss.get("pronunciation", ss.get("voice_quality", 0)),
        "overall":       round(raw.get("composite_score", 0)),
    }

    features: dict = {}
    pauses = []
    low_conf_words = []

    for task in raw.get("tasks", []):
        m = task.get("metrics", {})
        tid = task.get("task_id", "")

        if "word_error_rate" in m and "word_error_rate" not in features:
            features["word_error_rate"] = m["word_error_rate"]
        if "ddk_rate" in m:
            features["ddk_rate"] = m["ddk_rate"]
        if "rhythm_regularity" in m:
            features["rhythm_regularity"] = m["rhythm_regularity"]
        if "wpm" in m and "wpm" not in features:
            features["wpm"] = m["wpm"]
        if "pitch_std_hz" in m and "pitch_std" not in features:
            features["pitch_std"] = m["pitch_std_hz"]

        # Approximate pause event from aggregate stats
        if m.get("max_pause_duration", 0) > 0 and m.get("pause_count", 0) > 0:
            pauses.append({
                "start":      1.0,
                "end":        1.0 + m["max_pause_duration"],
                "duration":   m["max_pause_duration"],
                "after_word": "unknown",
            })

        for w in m.get("low_confidence_words", []):
            low_conf_words.append({
                "word":       w["word"],
                "time":       0.0,
                "confidence": w["confidence"],
            })

    # Fill gaps with neutral defaults (voice quality metrics were dropped from pipeline)
    features.setdefault("word_error_rate", 0.0)
    features.setdefault("ddk_rate", 5.0)
    features.setdefault("rhythm_regularity", 0.5)
    features.setdefault("wpm", 120)
    features.setdefault("pitch_std", 20.0)
    features["jitter"]  = 0.8
    features["shimmer"] = 2.0
    features["hnr"]     = 20.0

    timestamp = raw.get("assessed_at", "")[:19].replace(":", "-").replace("T", "_")
    session_id = f"session_{timestamp}" if timestamp else "session_001"

    return {
        "user_id":    "speakeasy_user",
        "session_id": session_id,
        "scores":     scores,
        "features":   features,
        "events": {
            "pauses":               pauses,
            "low_confidence_words": low_conf_words,
        },
    }


raw_assessment = _load_latest_assessment()
assessment = _normalize(raw_assessment)

sender = Agent(
    name="test_sender",
    seed="test_sender_speechscore_hackathon_seed",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)


@sender.on_event("startup")
async def send_test_assessment(ctx: Context):
    ctx.logger.info("Sending assessment to orchestrator...")
    await ctx.send(
        orchestrator.address,
        AssessmentRequest(
            session_id=assessment["session_id"],
            assessment_json=json.dumps(assessment),
        ),
    )


@sender.on_message(model=ReportResponse)
async def receive_report(ctx: Context, sender_addr: str, msg: ReportResponse):
    ctx.logger.info("=" * 55)
    ctx.logger.info("REPORT RECEIVED")
    ctx.logger.info(f"Status  : {msg.status}")
    ctx.logger.info(f"PDF path: {msg.pdf_path}")
    ctx.logger.info(f"Summary : {msg.summary[:300]}...")
    ctx.logger.info("=" * 55)


bureau = Bureau(port=8010)
bureau.add(orchestrator)
bureau.add(sender)

if __name__ == "__main__":
    bureau.run()
