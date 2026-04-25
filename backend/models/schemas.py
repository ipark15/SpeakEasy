from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


class TranscriptWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: float


class PauseInfo(BaseModel):
    start: float
    end: float
    duration: float


class FillerEvent(BaseModel):
    word: str
    time: float


class FeatureResult(BaseModel):
    # Universal
    transcript: str
    word_timestamps: List[TranscriptWord]
    audio_duration: float
    pauses: List[PauseInfo]
    pause_count: int
    avg_pause_duration: float
    max_pause_duration: float

    # Fluency (free_speech + read_sentence)
    wpm: Optional[float] = None
    filler_count: Optional[int] = None
    filler_words: Optional[List[FillerEvent]] = None
    speaking_time_ratio: Optional[float] = None

    # Clarity (read_sentence)
    word_error_rate: Optional[float] = None

    # Rhythm (pataka)
    syllable_intervals: Optional[List[float]] = None
    rhythm_regularity: Optional[float] = None
    ddk_rate: Optional[float] = None

    # Prosody — parselmouth (all tasks)
    pitch_mean: Optional[float] = None
    pitch_std: Optional[float] = None
    pitch_contour: Optional[List[float]] = None
    pitch_times: Optional[List[float]] = None
    jitter: Optional[float] = None
    shimmer: Optional[float] = None
    hnr: Optional[float] = None
    energy_mean: Optional[float] = None
    energy_std: Optional[float] = None

    # Pronunciation — Whisper confidence
    avg_word_confidence: Optional[float] = None
    low_confidence_words: Optional[List[dict]] = None


class ScoreBreakdown(BaseModel):
    fluency: Optional[float] = None
    clarity: Optional[float] = None
    rhythm: Optional[float] = None
    prosody: Optional[float] = None
    voice_quality: Optional[float] = None
    pronunciation: Optional[float] = None
    overall: float


class AssessmentResponse(BaseModel):
    task: str
    features: FeatureResult
    scores: ScoreBreakdown
    feedback: str
    tips: List[str]
    audio_duration: float
    session_id: Optional[str] = None
    assessment_id: Optional[str] = None
