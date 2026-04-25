from __future__ import annotations
from typing import Optional
from backend.db import get_client
from backend.models.schemas import AssessmentResponse


def create_session(user_id: str) -> str:
    """Insert a new in-progress session and return its id."""
    db = get_client()
    result = (
        db.table("sessions")
        .insert({"user_id": user_id, "status": "in_progress"})
        .execute()
    )
    return result.data[0]["id"]


def save_assessment(session_id: str, user_id: str, response: AssessmentResponse) -> str:
    """Persist one task's features, scores, and feedback. Returns the assessment id."""
    db = get_client()
    f = response.features
    s = response.scores

    row = {
        "session_id": session_id,
        "user_id": user_id,
        "task": response.task,
        "audio_duration": response.audio_duration,

        # Transcription
        "transcript": f.transcript,
        "word_timestamps": [w.model_dump() for w in f.word_timestamps],

        # Pauses
        "pause_count": f.pause_count,
        "avg_pause_duration": f.avg_pause_duration,
        "max_pause_duration": f.max_pause_duration,
        "pauses": [p.model_dump() for p in f.pauses],

        # Fluency
        "wpm": f.wpm,
        "filler_count": f.filler_count,
        "filler_words": [e.model_dump() for e in f.filler_words] if f.filler_words else None,
        "speaking_time_ratio": f.speaking_time_ratio,

        # Clarity
        "word_error_rate": f.word_error_rate,

        # Rhythm
        "syllable_intervals": f.syllable_intervals,
        "rhythm_regularity": f.rhythm_regularity,
        "ddk_rate": f.ddk_rate,

        # Prosody
        "pitch_mean": f.pitch_mean,
        "pitch_std": f.pitch_std,
        "pitch_contour": f.pitch_contour,
        "pitch_times": f.pitch_times,
        "jitter": f.jitter,
        "shimmer": f.shimmer,
        "hnr": f.hnr,
        "energy_mean": f.energy_mean,
        "energy_std": f.energy_std,

        # Pronunciation
        "avg_word_confidence": f.avg_word_confidence,
        "low_confidence_words": f.low_confidence_words,

        # Scores
        "score_fluency": s.fluency,
        "score_clarity": s.clarity,
        "score_rhythm": s.rhythm,
        "score_prosody": s.prosody,
        "score_voice_quality": s.voice_quality,
        "score_pronunciation": s.pronunciation,
        "score_overall": s.overall,

        # Feedback
        "feedback": response.feedback,
        "tips": response.tips,
    }

    result = db.table("assessments").insert(row).execute()
    return result.data[0]["id"]


def complete_session(session_id: str, overall_score: float) -> None:
    """Mark session complete and set final composite score."""
    from datetime import datetime, timezone
    db = get_client()
    db.table("sessions").update({
        "status": "complete",
        "overall_score": overall_score,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", session_id).execute()


def get_session(session_id: str) -> Optional[dict]:
    """Return session row + all its assessments."""
    db = get_client()
    session = (
        db.table("sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
        .data
    )
    if not session:
        return None

    assessments = (
        db.table("assessments")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
    )
    session["assessments"] = assessments
    return session


def save_coach_message(
    session_id: str,
    user_id: str,
    agent_type: str,
    role: str,
    content: str,
) -> None:
    db = get_client()
    db.table("coach_messages").insert({
        "session_id": session_id,
        "user_id": user_id,
        "agent_type": agent_type,
        "role": role,
        "content": content,
    }).execute()


def get_coach_history(session_id: str) -> list[dict]:
    """Return full chat history for a session, oldest first."""
    db = get_client()
    return (
        db.table("coach_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
        .data
    )
