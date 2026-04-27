from __future__ import annotations

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.db import queries as db
from backend.agents.therapist_agent.prompt_builder import build_system_prompt, build_first_message
from backend.agents.progress_tracker.agent import _fetch_history

load_dotenv()

router = APIRouter()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_BASE = "https://api.elevenlabs.io"


# ── /therapist/session — frontend calls this to start a live ElevenLabs session ──

class TherapistSessionRequest(BaseModel):
    session_id: str
    user_id: str


class TherapistSessionResponse(BaseModel):
    signed_url: str
    system_prompt: str
    first_message: str


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
                "pitch_std_hz", "avg_word_confidence", "transcript",
            )
            if a.get(k) is not None
        }
        tasks.append({"task_id": task_id, "scores": scores, "metrics": metrics})
        for k, v in scores.items():
            scores_sum.setdefault(k, []).append(v)

    scores_summary = {
        k: round(sum(vals) / len(vals), 1)
        for k, vals in scores_sum.items()
        if k not in ("voice_quality", "overall")
    }

    return {
        "session_id": session.get("id", ""),
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

    assessment_summary = _build_assessment_summary(session)
    history = _fetch_history(req.user_id, exclude_session_id=req.session_id)
    system_prompt = build_system_prompt(assessment_summary, history)
    first_message = build_first_message(assessment_summary)

    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}

    # Push personalized prompt directly onto the agent (server-side, no client override needed).
    try:
        patch_resp = httpx.patch(
            f"{ELEVENLABS_BASE}/v1/convai/agents/{ELEVENLABS_AGENT_ID}",
            headers=headers,
            json={"conversation_config": {"agent": {"prompt": {"prompt": system_prompt}}, "tts": {"voice_id": "q0PCqBlLEWqtUZJ2DYn7"}}},
            timeout=30.0,
        )
        patch_resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs agent update error {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs agent update failed: {e}")

    # Now get the signed URL — session will use the prompt we just set
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

    return TherapistSessionResponse(
        signed_url=signed_url,
        system_prompt=system_prompt,
        first_message=first_message,
    )


# ── /therapist/prompt — agent chain calls this after progress_tracker has run ──

class TherapistPromptRequest(BaseModel):
    current_assessment: dict
    history: dict


class TherapistPromptResponse(BaseModel):
    system_prompt: str
    first_message: str


@router.post("/therapist/prompt", response_model=TherapistPromptResponse)
def get_therapist_prompt(body: TherapistPromptRequest):
    """
    Returns system prompt + opening line for Maya without touching ElevenLabs.
    Call this after assessment completes and progress_tracker has run.
    """
    if not body.current_assessment:
        raise HTTPException(status_code=400, detail="current_assessment is required")

    return TherapistPromptResponse(
        system_prompt=build_system_prompt(body.current_assessment, body.history),
        first_message=build_first_message(body.current_assessment),
    )
