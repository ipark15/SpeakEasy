from __future__ import annotations
from typing import Optional
from backend.db import get_client
from backend.models.schemas import AssessmentResponse


def upload_audio(session_id: str, task: str, audio_bytes: bytes) -> Optional[str]:
    """Upload audio bytes to Supabase Storage. Returns public URL or None on failure."""
    try:
        db = get_client()
        path = f"{session_id}/{task}.wav"
        db.storage.from_("audio").upload(
            path=path,
            file=audio_bytes,
            file_options={"content-type": "audio/wav", "upsert": "true"},
        )
        return db.storage.from_("audio").get_public_url(path)
    except Exception:
        return None


def create_session(user_id: str) -> str:
    """Insert a new in-progress session and return its id."""
    db = get_client()
    result = (
        db.table("sessions")
        .insert({"user_id": user_id, "status": "in_progress"})
        .execute()
    )
    return result.data[0]["id"]


def save_assessment(session_id: str, user_id: str, response: AssessmentResponse, audio_url: Optional[str] = None) -> str:
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

        # Audio file
        "audio_url": audio_url,
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


# ── Profile ───────────────────────────────────────────────────

def upsert_profile(user_id: str, display_name: str = None, goals: dict = None) -> dict:
    db = get_client()
    payload = {"id": user_id}
    if display_name is not None:
        payload["display_name"] = display_name
    if goals is not None:
        payload["goals"] = goals
    result = db.table("user_profiles").upsert(payload).execute()
    return result.data[0]


def get_profile(user_id: str) -> Optional[dict]:
    db = get_client()
    result = (
        db.table("user_profiles")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Dashboard ─────────────────────────────────────────────────

def get_dashboard_data(user_id: str) -> dict:
    """Return trend data, streaks, and goals for the dashboard."""
    from datetime import date, timedelta

    db = get_client()

    # All completed sessions with their assessments
    sessions = (
        db.table("sessions")
        .select("id, created_at, overall_score, status")
        .eq("user_id", user_id)
        .eq("status", "complete")
        .order("created_at")
        .execute()
        .data
    )

    assessments = (
        db.table("assessments")
        .select(
            "session_id, task, created_at, audio_duration,"
            "score_fluency, score_clarity, score_rhythm, score_prosody,"
            "score_voice_quality, score_pronunciation, score_overall,"
            "wpm, word_error_rate, ddk_rate, jitter, shimmer, hnr,"
            "pitch_mean, pitch_std, avg_word_confidence"
        )
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
        .data
    )

    profile = get_profile(user_id)

    # Compute streaks from distinct session dates
    session_dates = sorted({
        date.fromisoformat(s["created_at"][:10]) for s in sessions
    })

    current_streak = 0
    longest_streak = 0
    if session_dates:
        today = date.today()
        # current streak: count back from today
        check = today
        for d in reversed(session_dates):
            if d == check:
                current_streak += 1
                check -= timedelta(days=1)
            elif d < check:
                break

        # longest streak
        run = 1
        for i in range(1, len(session_dates)):
            if session_dates[i] - session_dates[i - 1] == timedelta(days=1):
                run += 1
                longest_streak = max(longest_streak, run)
            else:
                run = 1
        longest_streak = max(longest_streak, run)

    return {
        "sessions": sessions,
        "assessments": assessments,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "goals": profile.get("goals") if profile else None,
        "display_name": profile.get("display_name") if profile else None,
    }


def get_history_data(user_id: str) -> dict:
    """Return per-session sub-score averages for the history page."""
    from collections import defaultdict

    db = get_client()

    sessions = (
        db.table("sessions")
        .select("id, created_at, overall_score")
        .eq("user_id", user_id)
        .eq("status", "complete")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
        .data
    )

    if not sessions:
        return {"sessions": [], "improvement": 0, "best_score": 0}

    session_ids = [s["id"] for s in sessions]
    assessments = (
        db.table("assessments")
        .select("session_id, score_fluency, score_clarity, score_rhythm, score_prosody, score_voice_quality")
        .in_("session_id", session_ids)
        .execute()
        .data
    )

    by_session: dict = defaultdict(list)
    for a in assessments:
        by_session[a["session_id"]].append(a)

    def _avg(vals: list) -> Optional[int]:
        nums = [v for v in vals if v is not None]
        return round(sum(nums) / len(nums)) if nums else None

    result_sessions = []
    for s in sessions:
        sid = s["id"]
        tasks = by_session[sid]
        result_sessions.append({
            "id": sid,
            "type": "General",
            "created_at": s["created_at"][:10],
            "overall_score": round(s["overall_score"]) if s.get("overall_score") is not None else 0,
            "fluency": _avg([t.get("score_fluency") for t in tasks]),
            "clarity": _avg([t.get("score_clarity") for t in tasks]),
            "rhythm": _avg([t.get("score_rhythm") for t in tasks]),
            "prosody": _avg([t.get("score_prosody") for t in tasks]),
            "voice_quality": _avg([t.get("score_voice_quality") for t in tasks]),
        })

    all_scores = [s["overall_score"] for s in sessions if s.get("overall_score") is not None]
    best_score = round(max(all_scores)) if all_scores else 0
    # sessions are desc-ordered: index 0 is newest, -1 is oldest
    improvement = round(all_scores[0] - all_scores[-1]) if len(all_scores) >= 2 else 0

    return {"sessions": result_sessions, "improvement": improvement, "best_score": best_score}
