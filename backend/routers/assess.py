from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from backend.models.schemas import AssessmentResponse, FeatureResult, TranscriptWord
from backend.services import feature_extraction as fe
from backend.services.scoring import compute_scores
from backend.services.transcription import transcribe
from backend.utils.audio import bytes_to_array, cleanup_temp, save_temp_wav
import backend.db.queries as db

router = APIRouter()

ALL_TASKS = {"read_sentence", "pataka", "free_speech"}
_TASK_WEIGHTS = {"read_sentence": 0.40, "pataka": 0.20, "free_speech": 0.40}

import os as _os
_ASSESSMENT_AGENT_ADDRESS = _os.getenv("ASSESSMENT_AGENT_ADDRESS", "")


def _build_assessment_payload(session_id: str, session_data: dict) -> dict:
    """Convert raw DB session rows into the 3-task JSON format the orchestrator expects."""
    assessments = session_data.get("assessments", [])
    scores_summary: dict[str, list] = {}
    tasks = []

    for a in assessments:
        tid = a["task"]
        scores = {k.replace("score_", ""): v for k, v in a.items()
                  if k.startswith("score_") and v is not None}
        metrics: dict = {}
        for key in ("wpm", "word_error_rate", "pause_count", "max_pause_duration",
                    "filler_count", "speech_rate_cv", "ddk_rate", "rhythm_regularity",
                    "pitch_mean", "pitch_std", "avg_word_confidence", "audio_duration"):
            if a.get(key) is not None:
                metrics[key] = a[key]
        if tid != "pataka" and a.get("low_confidence_words"):
            metrics["low_confidence_words"] = a["low_confidence_words"]
        if a.get("transcript"):
            metrics["transcript"] = a["transcript"]

        tasks.append({"task_id": tid, "scores": scores, "metrics": metrics})
        for dim, val in scores.items():
            if dim != "overall":
                scores_summary.setdefault(dim, []).append(val)

    composite_total = composite_w = 0.0
    for a in assessments:
        w = _TASK_WEIGHTS.get(a["task"], 0.33)
        if a.get("score_overall") is not None:
            composite_total += a["score_overall"] * w
            composite_w += w

    return {
        "session_id": session_id,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "composite_score": round(composite_total / composite_w, 1) if composite_w > 0 else 0.0,
        "scores_summary": {
            dim: round(sum(vals) / len(vals), 1)
            for dim, vals in scores_summary.items()
        },
        "tasks": tasks,
    }


async def _trigger_assessment_agent(session_id: str, session_data: dict) -> None:
    """Forward completed assessment scores to the Assessment Agent on Agentverse."""
    if not _ASSESSMENT_AGENT_ADDRESS:
        return
    try:
        from uuid import uuid4
        from uagents.communication import send_message
        from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

        payload = _build_assessment_payload(session_id, session_data)
        msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=json.dumps(payload))],
        )
        await send_message(destination=_ASSESSMENT_AGENT_ADDRESS, message=msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Assessment agent trigger failed: {e}")


# ── Session start ─────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    user_id: str


@router.post("/session/start")
def session_start(body: SessionStartRequest):
    session_id = db.create_session(body.user_id)
    return {"session_id": session_id}


@router.get("/session/{session_id}")
def session_get(session_id: str):
    from fastapi import HTTPException
    data = db.get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found.")
    for a in data.get("assessments", []):
        a["scores"] = {
            "fluency":       a.get("score_fluency"),
            "clarity":       a.get("score_clarity"),
            "rhythm":        a.get("score_rhythm"),
            "prosody":       a.get("score_prosody"),
            "voice_quality": a.get("score_voice_quality"),
            "pronunciation": a.get("score_pronunciation"),
            "overall":       a.get("score_overall"),
        }
    return data


# ── Clinical Report PDF ───────────────────────────────────────

@router.get("/report/{session_id}")
async def get_report(session_id: str):
    import os
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    pdf_path = f"backend/reports/{session_id}.pdf"

    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"speech_report_{session_id[:8]}.pdf",
        )

    raise HTTPException(
        status_code=404,
        detail="Report not ready yet — agents are still generating it. Please try again in a few seconds.",
    )


# ── Assess ────────────────────────────────────────────────────

@router.post("/assess", response_model=AssessmentResponse)
async def assess(
    audio: UploadFile = File(...),
    task: str = Form(...),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None),
    word_timestamps: Optional[str] = Form(None),
):
    audio_bytes = await audio.read()
    audio_array = bytes_to_array(audio_bytes)
    duration = len(audio_array) / 16000.0
    wav_path = save_temp_wav(audio_array)

    try:
        if transcript and word_timestamps:
            words = [TranscriptWord(**w) for w in json.loads(word_timestamps)]
            text = transcript
        else:
            text, words = transcribe(wav_path, task=task)

        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)

        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = filler_events = filler_count = wer = None
        acoustic_filler_count = None
        speech_rate_cv = None
        pataka_data: dict = {}

        if task == "read_sentence":
            wpm = fe.calculate_wpm(words, duration)
            wer = fe.calculate_wer(fe.READ_SENTENCE, text)

        elif task == "pataka":
            pataka_data = fe.analyze_pataka(audio_array)

        elif task == "free_speech":
            wpm = fe.calculate_wpm(words, duration)
            filler_list = fe.detect_fillers(words)
            filler_count = len(filler_list)
            filler_events = filler_list
            acoustic_filler_count = fe.detect_acoustic_fillers(wav_path)
            speech_rate_cv = fe.speech_rate_variation(words)

        features = FeatureResult(
            transcript=text,
            word_timestamps=words,
            audio_duration=duration,
            pauses=pauses,
            pause_count=len(pauses),
            avg_pause_duration=avg_pause,
            max_pause_duration=max_pause,
            wpm=wpm,
            filler_count=filler_count,
            acoustic_filler_count=acoustic_filler_count,
            filler_words=filler_events,
            speech_rate_cv=speech_rate_cv,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        scores = compute_scores(features, task)

        response = AssessmentResponse(
            task=task,
            features=features,
            scores=scores,
            feedback="",
            tips=[],
            audio_duration=duration,
            session_id=session_id,
        )

        # Persist to DB if session context provided
        assessment_id = None
        if user_id and session_id:
            audio_url = db.upload_audio(session_id, task, audio_bytes)
            assessment_id = db.save_assessment(session_id, user_id, response, audio_url=audio_url)
            response.assessment_id = assessment_id

            # Mark session complete when all 3 tasks have been saved
            session_data = db.get_session(session_id)
            completed_tasks = {a["task"] for a in session_data.get("assessments", [])}
            if ALL_TASKS.issubset(completed_tasks):
                all_scores = [
                    a["score_overall"] for a in session_data["assessments"]
                    if a.get("score_overall") is not None
                ]
                total = weight_sum = 0.0
                for a in session_data["assessments"]:
                    w = _TASK_WEIGHTS.get(a["task"], 0.33)
                    if a.get("score_overall") is not None:
                        total += a["score_overall"] * w
                        weight_sum += w
                overall = round(total / weight_sum, 1) if weight_sum > 0 else 0.0
                db.complete_session(session_id, overall)

                # Fire-and-forget: send assessment to orchestrator agent
                asyncio.create_task(_trigger_assessment_agent(session_id, session_data))

        return response
    finally:
        cleanup_temp(wav_path)


# ── Drill assess ──────────────────────────────────────────────
# Single free-speech recording scored across all 5 dimensions.
# Used by coach agents to evaluate user's drill performance.

class DrillScoreResponse(BaseModel):
    scores: dict
    transcript: str
    audio_duration: float


@router.post("/assess_drill", response_model=DrillScoreResponse)
async def assess_drill(
    audio: UploadFile = File(...),
    reference_phrase: Optional[str] = Form(None),  # phrase the coach gave — used for WER
    transcript: Optional[str] = Form(None),
    word_timestamps: Optional[str] = Form(None),
):
    audio_bytes = await audio.read()
    audio_array = bytes_to_array(audio_bytes)
    duration = len(audio_array) / 16000.0
    wav_path = save_temp_wav(audio_array)

    try:
        if transcript and word_timestamps:
            words = [TranscriptWord(**w) for w in json.loads(word_timestamps)]
            text = transcript
        else:
            text, words = transcribe(wav_path, task="free_speech")

        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)

        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = fe.calculate_wpm(words, duration)
        filler_list = fe.detect_fillers(words)
        filler_count = len(filler_list)
        acoustic_filler_count = fe.detect_acoustic_fillers(wav_path)
        speech_rate_cv = fe.speech_rate_variation(words)
        pataka_data = fe.analyze_pataka(audio_array)

        # WER against coach-provided phrase if given, else None
        wer = fe.calculate_wer(reference_phrase, text) if reference_phrase else None

        features = FeatureResult(
            transcript=text,
            word_timestamps=words,
            audio_duration=duration,
            pauses=pauses,
            pause_count=len(pauses),
            avg_pause_duration=avg_pause,
            max_pause_duration=max_pause,
            wpm=wpm,
            filler_count=filler_count,
            acoustic_filler_count=acoustic_filler_count,
            filler_words=filler_list,
            speech_rate_cv=speech_rate_cv,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        # Score all 5 dimensions — each uses whatever features are available
        from backend.services.scoring import (
            score_fluency, score_clarity, score_rhythm, score_prosody, score_pronunciation
        )
        scores = {
            "fluency":       score_fluency(features, is_read_sentence=False),
            "clarity":       score_clarity(features) if wer is not None else None,
            "rhythm":        score_rhythm(features),
            "prosody":       score_prosody(features, weight_cv=True),
            "pronunciation": score_pronunciation(features),
        }
        # Strip None values
        scores = {k: v for k, v in scores.items() if v is not None}

        return DrillScoreResponse(
            scores=scores,
            transcript=text,
            audio_duration=duration,
        )
    finally:
        cleanup_temp(wav_path)
