from __future__ import annotations
from faster_whisper import WhisperModel
from backend.models.schemas import TranscriptWord

# Loaded once at module level — stays warm between requests
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        print("  [whisper] Loading model (first call only)...")
        _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model


def transcribe(wav_path: str) -> tuple[str, list[TranscriptWord]]:
    model = _get_model()
    segments, _ = model.transcribe(
        wav_path,
        beam_size=5,
        word_timestamps=True,
        language="en",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
    )
    words: list[TranscriptWord] = []
    text_parts: list[str] = []
    for seg in segments:
        for w in (seg.words or []):
            cleaned = w.word.strip()
            if cleaned:
                words.append(TranscriptWord(
                    word=cleaned,
                    start=w.start,
                    end=w.end,
                    confidence=w.probability,
                ))
                text_parts.append(cleaned)
    return " ".join(text_parts), words
