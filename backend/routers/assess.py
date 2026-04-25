from __future__ import annotations
import json
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, UploadFile

from backend.models.schemas import AssessmentResponse, FeatureResult, TranscriptWord
from backend.services import feature_extraction as fe
from backend.services.scoring import compute_scores
from backend.services.transcription import transcribe
from backend.utils.audio import bytes_to_array, cleanup_temp, save_temp_wav

router = APIRouter()


@router.post("/assess", response_model=AssessmentResponse)
async def assess(
    audio: UploadFile = File(...),
    task: str = Form(...),
    user_id: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None),
    word_timestamps: Optional[str] = Form(None),
):
    audio_bytes = await audio.read()
    audio_array = bytes_to_array(audio_bytes)
    duration = len(audio_array) / 16000.0
    wav_path = save_temp_wav(audio_array)

    try:
        # Transcription — skip if ZETIC pre-computed it
        if transcript and word_timestamps:
            words = [TranscriptWord(**w) for w in json.loads(word_timestamps)]
            text = transcript
        else:
            text, words = transcribe(wav_path)

        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)

        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = filler_events = filler_count = wer = None
        speaking_ratio = None
        pataka_data: dict = {}

        if task == "read_sentence":
            wpm = fe.calculate_wpm(words, duration)
            wer = fe.calculate_wer(fe.READ_SENTENCE, text)
            speaking_ratio = fe.speaking_time_ratio(words, duration)
        elif task == "pataka":
            pataka_data = fe.analyze_pataka(audio_array)
        elif task == "free_speech":
            wpm = fe.calculate_wpm(words, duration)
            filler_list = fe.detect_fillers(words)
            filler_count = len(filler_list)
            filler_events = filler_list
            speaking_ratio = fe.speaking_time_ratio(words, duration)

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
            filler_words=filler_events,
            speaking_time_ratio=speaking_ratio,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        scores = compute_scores(features, task)

        return AssessmentResponse(
            task=task,
            features=features,
            scores=scores,
            feedback="",   # Gemma feedback wired in next phase
            tips=[],
            audio_duration=duration,
        )
    finally:
        cleanup_temp(wav_path)
