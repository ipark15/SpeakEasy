import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.db import queries as db
from backend.agents.therapist_agent.gemma_client import build_system_prompt

load_dotenv()

router = APIRouter()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_BASE = "https://api.elevenlabs.io"


class TherapistSessionRequest(BaseModel):
    session_id: str
    user_id: str


class TherapistSessionResponse(BaseModel):
    signed_url: str
    system_prompt: str


def _build_assessment_summary(session: dict) -> dict:
    assessments = session.get("assessments", [])

    scores_sum: dict[str, list[float]] = {}
    tasks = []

    for a in assessments:
        task_id = a.get("task", "unknown")
        scores = {
            k: a.get(f"score_{k}")
            for k in ("fluency", "clarity", "rhythm", "prosody", "pronunciation", "voice_quality")
            if a.get(f"score_{k}") is not None
        }
        metrics = {
            k: a.get(k)
            for k in (
                "wpm", "filler_count", "pause_count", "max_pause_duration",
                "word_error_rate", "ddk_rate", "rhythm_regularity",
                "pitch_std_hz", "avg_word_confidence",
            )
            if a.get(k) is not None
        }
        tasks.append({"task_id": task_id, "scores": scores, "metrics": metrics})
        for k, v in scores.items():
            scores_sum.setdefault(k, []).append(v)

    scores_summary = {
        k: round(sum(vals) / len(vals), 1)
        for k, vals in scores_sum.items()
    }

    return {
        "composite_score": session.get("overall_score"),
        "scores_summary": scores_summary,
        "tasks": tasks,
    }


@router.post("/therapist/session", response_model=TherapistSessionResponse)
def start_therapist_session(req: TherapistSessionRequest):
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
    if not ELEVENLABS_AGENT_ID:
        raise HTTPException(status_code=500, detail="ELEVENLABS_AGENT_ID not configured")

    session = db.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = db.get_history_data(req.user_id)
    assessment_summary = _build_assessment_summary(session)
    system_prompt = build_system_prompt(assessment_summary, history)

    try:
        resp = httpx.get(
            f"{ELEVENLABS_BASE}/v1/convai/conversation/get_signed_url",
            params={"agent_id": ELEVENLABS_AGENT_ID},
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=30.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs request failed: {e}")

    data = resp.json()
    signed_url = data.get("signed_url", "")
    if not signed_url:
        raise HTTPException(status_code=502, detail=f"ElevenLabs response missing signed_url: {data}")

    return TherapistSessionResponse(signed_url=signed_url, system_prompt=system_prompt)
